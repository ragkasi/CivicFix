"""AI triage service — orchestrates classification, analysis storage, and embeddings."""
import asyncio
import logging
from uuid import UUID

from app.ai.classify import classify_report
from app.ai.embeddings import build_embedding_text, generate_embedding
from app.db.supabase import get_supabase_client
from app.schemas.reports import AIAnalysisResponse

logger = logging.getLogger(__name__)


def _run(fn):
    return asyncio.to_thread(fn)


class AIService:
    def _client(self):
        return get_supabase_client()

    # ─── Full pipeline ────────────────────────────────────────────────────────

    async def run_pipeline(self, report_id: str) -> None:
        """Run the complete AI triage pipeline for a report.

        Designed to be called as a FastAPI BackgroundTask — logs errors
        and returns cleanly rather than letting exceptions propagate.
        """
        try:
            client = self._client()

            # 1. Load report
            report_res = await _run(
                lambda: client.table("reports")
                .select("id, description, category, address, latitude, longitude")
                .eq("id", report_id)
                .limit(1)
                .execute()
            )
            if not report_res.data:
                logger.error(f"AI pipeline: report {report_id} not found")
                return
            report = report_res.data[0]

            # 2. Load image public_url if available
            img_res = await _run(
                lambda: client.table("report_images")
                .select("public_url")
                .eq("report_id", report_id)
                .limit(1)
                .execute()
            )
            image_url = (
                img_res.data[0].get("public_url")
                if img_res.data and img_res.data[0].get("public_url")
                else None
            )

            # 3. Classify
            classification = await classify_report(
                description=report["description"],
                image_url=image_url,
                address=report.get("address"),
                latitude=report.get("latitude"),
                longitude=report.get("longitude"),
            )

            # 4. Resolve department slug → ID
            dept_id = await self._resolve_dept_slug(classification["department_slug"])

            # 5. Upsert ai_analysis row
            settings = _get_settings_safe()
            analysis_row = {
                "report_id": report_id,
                "ai_category": classification["category"],
                "ai_severity": classification["severity"],
                "ai_department": classification["department_slug"],
                "ai_summary": classification["summary"],
                "recommended_action": classification["recommended_action"],
                "confidence_score": classification["confidence"],
                "reasoning": {
                    "model": settings.get("ai_model", "gpt-4o"),
                    "has_image": image_url is not None,
                },
            }
            await _run(
                lambda: client.table("ai_analysis")
                .upsert(analysis_row, on_conflict="report_id")
                .execute()
            )

            # 6. Update report.category / .severity (and optionally department_id)
            update: dict = {
                "category": classification["category"],
                "severity": classification["severity"],
            }
            if dept_id:
                update["department_id"] = dept_id

            await _run(
                lambda: client.table("reports")
                .update(update)
                .eq("id", report_id)
                .execute()
            )

            # 7. Generate and store embedding
            embed_text = build_embedding_text(
                description=report["description"],
                category=classification["category"],
                severity=classification["severity"],
                address=report.get("address"),
                summary=classification["summary"],
            )
            embedding = await generate_embedding(embed_text)
            if embedding:
                await _run(
                    lambda: client.table("report_embeddings")
                    .upsert({"report_id": report_id, "embedding": embedding}, on_conflict="report_id")
                    .execute()
                )

            # 8. Duplicate detection (runs after embedding is stored)
            if embedding:
                try:
                    from app.services.duplicate_service import DuplicateService
                    dup_service = DuplicateService()
                    duplicates = await dup_service.find_duplicates(report_id)
                    logger.info(
                        f"Duplicate detection: report={report_id} found={len(duplicates)} candidates"
                    )
                except Exception as dup_exc:
                    # Duplicate detection failure must not cancel the AI analysis results
                    logger.warning(f"Duplicate detection failed for {report_id}: {dup_exc}")

            logger.info(
                f"AI pipeline done: report={report_id} "
                f"category={classification['category']} "
                f"severity={classification['severity']} "
                f"confidence={classification['confidence']:.2f}"
            )

        except Exception as exc:
            logger.error(f"AI pipeline failed for report {report_id}: {exc}")

    # ─── Manual analysis / re-analysis ───────────────────────────────────────

    async def analyze_report(self, report_id: str) -> AIAnalysisResponse | None:
        """Run pipeline synchronously and return the stored AIAnalysis.

        Used by POST /api/reports/{id}/analyze.
        Returns None if the report does not exist.
        """
        client = self._client()

        # Verify report exists first
        check = await _run(
            lambda: client.table("reports")
            .select("id")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
        if not check.data:
            return None

        await self.run_pipeline(report_id)
        return await self.get_ai_analysis(report_id)

    async def get_ai_analysis(self, report_id: str) -> AIAnalysisResponse | None:
        """Fetch the stored AI analysis for a report."""
        client = self._client()
        result = await _run(
            lambda: client.table("ai_analysis")
            .select("*")
            .eq("report_id", report_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        return AIAnalysisResponse(
            id=row["id"],
            report_id=row["report_id"],
            ai_category=row.get("ai_category"),
            ai_severity=row.get("ai_severity"),
            ai_department=row.get("ai_department"),
            ai_summary=row.get("ai_summary"),
            recommended_action=row.get("recommended_action"),
            confidence_score=row.get("confidence_score"),
            reasoning=row.get("reasoning"),
            created_at=row["created_at"],
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    async def _resolve_dept_slug(self, slug: str) -> str | None:
        client = self._client()
        result = await _run(
            lambda: client.table("departments")
            .select("id")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
        return result.data[0]["id"] if result.data else None


def _get_settings_safe() -> dict:
    """Return a dict of settings values without raising on missing config."""
    try:
        from app.config import get_settings
        s = get_settings()
        return {"ai_model": s.ai_model}
    except Exception:
        return {"ai_model": "gpt-4o"}
