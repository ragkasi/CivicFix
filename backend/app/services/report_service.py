"""
Report service.

Phase 1: All methods are stubs that return empty results or raise
NotImplementedError. Full database logic is implemented in Phase 3.
"""
from uuid import UUID

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


class ReportService:
    async def create_report(self, data: CreateReportRequest) -> ReportResponse:
        # Phase 3: validate input, persist report, store image in Supabase Storage,
        # generate public_tracking_token, trigger AI pipeline as background task.
        raise NotImplementedError("Report creation is implemented in Phase 3")

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
        # Phase 3: query reports with Supabase filters, bbox PostGIS filtering,
        # and pagination.
        return []

    async def get_report(self, report_id: UUID) -> ReportDetailResponse | None:
        # Phase 3: fetch report with AI analysis, images, and status history.
        return None

    async def update_status(
        self, report_id: UUID, data: UpdateStatusRequest
    ) -> ReportDetailResponse | None:
        # Phase 3: persist status change, append event to status_events table,
        # trigger resident notification.
        return None

    async def assign_department(
        self, report_id: UUID, data: AssignDepartmentRequest
    ) -> ReportDetailResponse | None:
        # Phase 3: set department_id on report, log status event.
        return None

    async def get_report_by_tracking_token(
        self, token: str
    ) -> TrackingResponse | None:
        # Phase 3: fetch resident-safe view using public_tracking_token.
        # Never expose internal admin notes or private contact info.
        return None
