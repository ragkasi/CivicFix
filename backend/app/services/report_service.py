"""Report service — Phase 5 complete implementation."""
import asyncio
from uuid import UUID

from app.db.supabase import get_supabase_client
from app.schemas.geospatial import NearbyReportResponse
from app.schemas.reports import (
    AIAnalysisResponse,
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


def _parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    """Parse 'minLng,minLat,maxLng,maxLat' into four floats.

    Raises ValueError with a clear message for invalid input.
    """
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError(
            "bbox must be 'minLng,minLat,maxLng,maxLat' (4 comma-separated numbers)"
        )
    try:
        min_lng, min_lat, max_lng, max_lat = map(float, parts)
    except ValueError:
        raise ValueError("All bbox values must be numeric")
    if not (-180 <= min_lng <= 180 and -180 <= max_lng <= 180):
        raise ValueError("Longitude values must be between -180 and 180")
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise ValueError("Latitude values must be between -90 and 90")
    return min_lng, min_lat, max_lng, max_lat


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
        """Fetch full report detail including images, status events, AI analysis, and department."""
        client = self._client()

        # Join departments via FK
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

        # Parallel fetch of images, status events, and AI analysis
        images_res, events_res, analysis_res = await asyncio.gather(
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
            _run(
                lambda: client.table("ai_analysis")
                .select("*")
                .eq("report_id", str(report_id))
                .limit(1)
                .execute()
            ),
        )

        return self._to_detail_full(row, images_res.data, events_res.data, analysis_res.data)

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
        # When a bbox is provided, delegate to the PostGIS RPC function.
        # The RPC result does not include a departments join; department will be None.
        if bbox:
            min_lng, min_lat, max_lng, max_lat = _parse_bbox(bbox)
            return await self._list_in_bbox(min_lng, min_lat, max_lng, max_lat, limit)

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
            return q.execute()

        result = await _run(_query)
        return [self._to_detail(row) for row in result.data]

    async def _list_in_bbox(
        self,
        min_lng: float,
        min_lat: float,
        max_lng: float,
        max_lat: float,
        limit: int = 200,
    ) -> list[ReportDetailResponse]:
        """Fetch reports inside a bounding box using the reports_in_bbox RPC."""
        client = self._client()
        result = await _run(
            lambda: client.rpc(
                "reports_in_bbox",
                {
                    "min_lng": min_lng,
                    "min_lat": min_lat,
                    "max_lng": max_lng,
                    "max_lat": max_lat,
                    "result_limit": limit,
                },
            ).execute()
        )
        return [self._to_detail(row) for row in result.data]

    async def list_nearby_reports(
        self,
        lat: float,
        lng: float,
        radius_km: float = 1.0,
        limit: int = 50,
    ) -> list[NearbyReportResponse]:
        """Fetch reports within a radius using the nearby_reports RPC."""
        client = self._client()
        result = await _run(
            lambda: client.rpc(
                "nearby_reports",
                {
                    "input_lat": lat,
                    "input_lng": lng,
                    "radius_meters": radius_km * 1000,
                    "result_limit": limit,
                },
            ).execute()
        )
        return [
            NearbyReportResponse(
                id=row["id"],
                description=row["description"],
                category=row.get("category"),
                severity=row.get("severity"),
                status=row["status"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                address=row.get("address"),
                department_id=row.get("department_id"),
                tracking_token=row["public_tracking_token"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                distance_meters=row["distance_meters"],
            )
            for row in result.data
        ]

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
        analysis_rows: list[dict] | None = None,
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
        ai_analysis = None
        if analysis_rows:
            a = analysis_rows[0]
            ai_analysis = AIAnalysisResponse(
                id=a["id"],
                report_id=a["report_id"],
                ai_category=a.get("ai_category"),
                ai_severity=a.get("ai_severity"),
                ai_department=a.get("ai_department"),
                ai_summary=a.get("ai_summary"),
                recommended_action=a.get("recommended_action"),
                confidence_score=a.get("confidence_score"),
                reasoning=a.get("reasoning"),
                created_at=a["created_at"],
            )
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
            ai_analysis=ai_analysis,
        )
