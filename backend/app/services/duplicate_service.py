"""Duplicate detection service using pgvector + PostGIS."""
import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from app.db.supabase import get_supabase_client
from app.schemas.reports import DuplicateSuggestionResponse

logger = logging.getLogger(__name__)


def _run(fn):
    return asyncio.to_thread(fn)


# ─── Pure scoring helpers (no I/O — easy to unit-test) ────────────────────────


def calculate_combined_score(
    semantic_score: float,
    distance_meters: float,
    radius_meters: float,
    candidate_age_days: int,
) -> float:
    """Weighted combined score in [0, 1].

    Weights:  0.60 semantic · 0.25 location · 0.15 recency
    - semantic_score: 1 = identical, 0 = unrelated
    - location_score: 1 at distance=0, linear decay to 0 at radius edge
    - recency_score:  1 for today, linear decay to 0 at 30 days old
    """
    location_score = max(0.0, 1.0 - (distance_meters / max(radius_meters, 1)))
    recency_score = max(0.0, 1.0 - (candidate_age_days / 30.0))
    return 0.60 * semantic_score + 0.25 * location_score + 0.15 * recency_score


def build_reason(
    semantic_score: float,
    distance_meters: float,
    category: str | None = None,
) -> str:
    """Return a human-readable explanation for why this is a likely duplicate."""
    parts: list[str] = []

    if semantic_score >= 0.80:
        parts.append("very similar description")
    elif semantic_score >= 0.60:
        parts.append("similar description")
    elif semantic_score >= 0.40:
        parts.append("somewhat similar description")

    if distance_meters < 50:
        parts.append("same location")
    elif distance_meters < 200:
        parts.append("very close proximity")
    elif distance_meters < 500:
        parts.append("nearby")

    return "; ".join(parts) if parts else "moderate overall similarity"


# ─── Service ──────────────────────────────────────────────────────────────────


class DuplicateService:
    def _client(self):
        return get_supabase_client()

    async def find_duplicates(
        self,
        report_id: str,
        radius_meters: float = 500.0,
        similarity_threshold: float = 0.35,
        limit: int = 5,
    ) -> list[DuplicateSuggestionResponse]:
        """Find likely duplicate reports using the find_duplicate_candidates RPC.

        Returns empty list gracefully when:
        - The report has no embedding (not yet processed by AI pipeline)
        - The report has no geom (missing lat/lng)
        - No candidates meet the similarity threshold
        """
        client = self._client()

        # Call the PostGIS + pgvector RPC function (fetch more than limit to allow filtering)
        try:
            rpc_result = await _run(
                lambda: client.rpc(
                    "find_duplicate_candidates",
                    {
                        "source_report_id": report_id,
                        "radius_meters": radius_meters,
                        "result_limit": limit * 3,
                    },
                ).execute()
            )
        except Exception as exc:
            logger.error(f"Duplicate detection RPC failed for {report_id}: {exc}")
            return []

        if not rpc_result.data:
            return []

        now = datetime.now(tz=timezone.utc)
        suggestions: list[DuplicateSuggestionResponse] = []

        for row in rpc_result.data:
            semantic = float(row["semantic_score"])
            distance = float(row["distance_meters"])

            # Parse candidate age
            raw_ts = row.get("candidate_created_at", "")
            try:
                ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                age_days = max(0, (now - ts).days)
            except Exception:
                age_days = 0

            combined = calculate_combined_score(semantic, distance, radius_meters, age_days)

            if combined < similarity_threshold:
                continue

            reason = build_reason(semantic, distance, row.get("candidate_category"))

            suggestions.append(
                DuplicateSuggestionResponse(
                    candidate_report_id=row["candidate_report_id"],
                    candidate_description=row.get("candidate_description"),
                    candidate_category=row.get("candidate_category"),
                    candidate_severity=row.get("candidate_severity"),
                    candidate_status=row.get("candidate_status"),
                    candidate_address=row.get("candidate_address"),
                    candidate_created_at=row.get("candidate_created_at"),
                    semantic_score=semantic,
                    distance_meters=distance,
                    combined_score=combined,
                    reason=reason,
                )
            )

        # Sort by combined score descending, take top N
        suggestions.sort(key=lambda s: s.combined_score, reverse=True)
        top = suggestions[:limit]

        # Persist suggestions to database (upsert to allow re-running)
        await self._store_suggestions(report_id, top)

        logger.info(
            f"Duplicate detection: report={report_id} "
            f"candidates_returned={len(rpc_result.data)} "
            f"above_threshold={len(suggestions)} stored={len(top)}"
        )
        return top

    async def get_stored_suggestions(
        self, report_id: str
    ) -> list[DuplicateSuggestionResponse]:
        """Fetch previously stored duplicate suggestions with candidate details."""
        client = self._client()

        suggestions_res = await _run(
            lambda: client.table("duplicate_suggestions")
            .select("*")
            .eq("report_id", report_id)
            .order("combined_score", desc=True)
            .execute()
        )

        if not suggestions_res.data:
            return []

        # Batch-fetch candidate report details
        candidate_ids = [row["candidate_report_id"] for row in suggestions_res.data]
        candidates_res = await _run(
            lambda: client.table("reports")
            .select("id, description, category, severity, status, address, created_at")
            .in_("id", candidate_ids)
            .execute()
        )
        candidates = {r["id"]: r for r in (candidates_res.data or [])}

        results: list[DuplicateSuggestionResponse] = []
        for row in suggestions_res.data:
            cid = row["candidate_report_id"]
            c = candidates.get(cid, {})
            results.append(
                DuplicateSuggestionResponse(
                    candidate_report_id=cid,
                    candidate_description=c.get("description"),
                    candidate_category=c.get("category"),
                    candidate_severity=c.get("severity"),
                    candidate_status=c.get("status"),
                    candidate_address=c.get("address"),
                    candidate_created_at=c.get("created_at"),
                    semantic_score=float(row.get("semantic_score") or 0),
                    distance_meters=float(row.get("distance_meters") or 0),
                    combined_score=float(row.get("combined_score") or 0),
                    reason=row.get("reason"),
                )
            )
        return results

    # ─── Private ──────────────────────────────────────────────────────────────

    async def _store_suggestions(
        self, report_id: str, suggestions: list[DuplicateSuggestionResponse]
    ) -> None:
        if not suggestions:
            return
        client = self._client()
        for s in suggestions:
            row = {
                "report_id": report_id,
                "candidate_report_id": str(s.candidate_report_id),
                "semantic_score": s.semantic_score,
                "distance_meters": s.distance_meters,
                "combined_score": s.combined_score,
                "reason": s.reason,
            }
            try:
                await _run(
                    lambda r=row: client.table("duplicate_suggestions")
                    .upsert(r, on_conflict="report_id,candidate_report_id")
                    .execute()
                )
            except Exception as exc:
                logger.warning(f"Could not store duplicate suggestion: {exc}")
