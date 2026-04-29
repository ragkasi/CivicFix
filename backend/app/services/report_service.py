"""Report service — Phase 4 complete implementation."""
import asyncio
from uuid import UUID

from app.db.supabase import get_supabase_client
from app.schemas.reports import (
    AssignDepartmentRequest,
    CreateReportRequest,
    DepartmentInfo,
    ReportCategory,
    ReportDetailResponse,
    ReportImageResponse,
    ReportResponse,
    ReportSeverity,
    ReportStatus,
    StatusEventResponse,
    UpdateStatusRequest,
)
from app.schemas.tracking import TrackingResponse


def _run(fn):
    return asyncio.to_thread(fn)


class ReportService:
    def _client(self):
        return get_supabase_client()

    # ─── Create ───────────────────────────────────────────────────────────────

    async def create_report(self, data: CreateReportRequest) -> ReportResponse:
        client = self._client()

        insert_data: dict = {
            "description": data.description,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "status": ReportStatus.submitted.value,
            "category": ReportCategory.other.value,
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

    # ─── Read ──────────────────────────────────────────────────────────────────

    async def get_report(self, report_id: UUID) -> ReportDetailResponse | None:
        """Fetch full report detail including images, status events, and department."""
        client = self._client()

        # Join departments via FK for the department object
        result = await _run(
            lambda: client.table("reports")
            .select("*, departments(id, slug, name)")
            .eq("id", str(report_id))
            .limit(1)
            .execute()
        )
        if not result.data:
            return None

        row = result.data[0]

        # Parallel fetch of images and status events
        images_res, events_res = await asyncio.gather(
            _run(
                lambda: client.table("report_images")
                .select("*")
                .eq("report_id", str(report_id))
                .order("created_at")
                .execute()
            ),
            _run(
                lambda: client.table("status_events")
                .select("*")
                .eq("report_id", str(report_id))
                .order("created_at")
                .execute()
            ),
        )

        return self._to_detail_full(row, images_res.data, events_res.data)

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

        def _query():
            q = (
                client.table("reports")
                .select("*, departments(id, slug, name)")
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
            # bbox filtering via PostGIS deferred to Phase 5 (map)
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
        client = self._client()

        # Fetch existing to get old_status and confirm existence
        existing = await _run(
            lambda: client.table("reports")
            .select("id, status")
            .eq("id", str(report_id))
            .limit(1)
            .execute()
        )
        if not existing.data:
            return None

        old_status = existing.data[0]["status"]

        # Update status on the report
        await _run(
            lambda: client.table("reports")
            .update({"status": data.status.value})
            .eq("id", str(report_id))
            .execute()
        )

        # Append to audit log
        event: dict = {
            "report_id": str(report_id),
            "old_status": old_status,
            "new_status": data.status.value,
        }
        if data.note:
            event["note"] = data.note
        if data.public_note:
            event["public_note"] = data.public_note

        await _run(lambda: client.table("status_events").insert(event).execute())

        return await self.get_report(report_id)

    async def assign_department(
        self, report_id: UUID, data: AssignDepartmentRequest
    ) -> ReportDetailResponse | None:
        client = self._client()

        # Verify report exists
        existing = await _run(
            lambda: client.table("reports")
            .select("id")
            .eq("id", str(report_id))
            .limit(1)
            .execute()
        )
        if not existing.data:
            return None

        # Verify department exists
        dept = await _run(
            lambda: client.table("departments")
            .select("id")
            .eq("id", str(data.department_id))
            .limit(1)
            .execute()
        )
        if not dept.data:
            raise ValueError(f"Department {data.department_id} not found")

        # Assign department
        await _run(
            lambda: client.table("reports")
            .update({"department_id": str(data.department_id)})
            .eq("id", str(report_id))
            .execute()
        )

        return await self.get_report(report_id)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _dept_from_row(row: dict) -> DepartmentInfo | None:
        d = row.get("departments")
        return DepartmentInfo(id=d["id"], slug=d["slug"], name=d["name"]) if d else None

    @staticmethod
    def _to_detail(row: dict) -> ReportDetailResponse:
        """Lightweight mapping used for list endpoints (no images/events)."""
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
            department=ReportService._dept_from_row(row),
            tracking_token=row["public_tracking_token"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _to_detail_full(
        row: dict,
        image_rows: list[dict],
        event_rows: list[dict],
    ) -> ReportDetailResponse:
        """Full mapping used for single-report detail endpoint."""
        images = [
            ReportImageResponse(
                id=img["id"],
                storage_path=img["storage_path"],
                public_url=img.get("public_url"),
                created_at=img["created_at"],
            )
            for img in image_rows
        ]
        events = [
            StatusEventResponse(
                id=ev["id"],
                old_status=ev.get("old_status"),
                new_status=ev["new_status"],
                note=ev.get("note"),
                public_note=ev.get("public_note"),
                created_at=ev["created_at"],
            )
            for ev in event_rows
        ]
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
            department=ReportService._dept_from_row(row),
            tracking_token=row["public_tracking_token"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            images=images,
            status_events=events,
        )
