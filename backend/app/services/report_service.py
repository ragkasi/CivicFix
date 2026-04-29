"""Report service — real implementation for Phase 3."""
import asyncio
from uuid import UUID

from app.db.supabase import get_supabase_client
from app.schemas.reports import (
    AssignDepartmentRequest,
    CreateReportRequest,
    ReportCategory,
    ReportDetailResponse,
    ReportResponse,
    ReportSeverity,
    ReportStatus,
    UpdateStatusRequest,
)
from app.schemas.tracking import TrackingResponse


def _run(fn):
    """Run a synchronous Supabase client call without blocking the event loop."""
    return asyncio.to_thread(fn)


class ReportService:
    def _client(self):
        return get_supabase_client()

    # ─── Create ──────────────────────────────────────────────────────────────

    async def create_report(self, data: CreateReportRequest) -> ReportResponse:
        client = self._client()

        insert_data: dict = {
            "description": data.description,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "status": ReportStatus.submitted.value,
            # Default category; AI pipeline overwrites this in Phase 4
            "category": ReportCategory.other.value,
            # severity left NULL; AI pipeline sets it in Phase 4
        }
        if data.address:
            insert_data["address"] = data.address
        if data.contact_email:
            insert_data["contact_email"] = data.contact_email
        if data.contact_phone:
            insert_data["contact_phone"] = data.contact_phone

        result = await _run(
            lambda: client.table("reports").insert(insert_data).execute()
        )

        if not result.data:
            raise RuntimeError("Database did not return the created report")

        row = result.data[0]

        # Store image reference if an uploaded image path was provided
        if data.image_path:
            await _run(
                lambda: client.table("report_images")
                .insert({"report_id": row["id"], "storage_path": data.image_path})
                .execute()
            )

        return ReportResponse(
            id=row["id"],
            status=row["status"],
            category=row.get("category"),
            tracking_token=row["public_tracking_token"],
            created_at=row["created_at"],
        )

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_report(self, report_id: UUID) -> ReportDetailResponse | None:
        client = self._client()
        result = await _run(
            lambda: client.table("reports")
            .select("*")
            .eq("id", str(report_id))
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return self._to_detail(result.data[0])

    async def list_reports(
        self,
        status: ReportStatus | None = None,
        category: ReportCategory | None = None,
        severity: ReportSeverity | None = None,
        department_id: UUID | None = None,
        bbox: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportDetailResponse]:
        client = self._client()

        # Build query with chained filters
        # bbox (minLng,minLat,maxLng,maxLat) filtering is done in Phase 4+
        # via PostGIS ST_MakeEnvelope — skipped here for simplicity.
        def _query():
            q = (
                client.table("reports")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
            )
            if status:
                q = q.eq("status", status.value)
            if category:
                q = q.eq("category", category.value)
            if severity:
                q = q.eq("severity", severity.value)
            if department_id:
                q = q.eq("department_id", str(department_id))
            return q.execute()

        result = await _run(_query)
        return [self._to_detail(row) for row in result.data]

    async def get_report_by_tracking_token(
        self, token: str
    ) -> TrackingResponse | None:
        client = self._client()
        result = await _run(
            lambda: client.table("reports")
            .select(
                "public_tracking_token, status, category, severity, "
                "address, created_at, updated_at"
                # Deliberately excludes contact_email, contact_phone,
                # internal admin notes, and private IDs.
            )
            .eq("public_tracking_token", token)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        return TrackingResponse(
            tracking_token=row["public_tracking_token"],
            status=row["status"],
            category=row.get("category"),
            severity=row.get("severity"),
            address=row.get("address"),
            created_at=row["created_at"],
            updated_at=row.get("updated_at"),
        )

    # ─── Update ───────────────────────────────────────────────────────────────

    async def update_status(
        self, report_id: UUID, data: UpdateStatusRequest
    ) -> ReportDetailResponse | None:
        # Phase 4: persist status change, append to status_events, trigger notification
        return None

    async def assign_department(
        self, report_id: UUID, data: AssignDepartmentRequest
    ) -> ReportDetailResponse | None:
        # Phase 4: set department_id, log status event
        return None

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_detail(row: dict) -> ReportDetailResponse:
        return ReportDetailResponse(
            id=row["id"],
            description=row["description"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            address=row.get("address"),
            status=row["status"],
            category=row.get("category"),
            severity=row.get("severity"),
            department_id=row.get("department_id"),
            tracking_token=row["public_tracking_token"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
