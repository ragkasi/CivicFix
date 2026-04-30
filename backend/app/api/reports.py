from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.schemas.geospatial import NearbyReportResponse
from app.schemas.reports import (
    AIAnalysisResponse,
    AssignDepartmentRequest,
    CreateReportRequest,
    DuplicateSuggestionResponse,
    ReportCategory,
    ReportDetailResponse,
    ReportResponse,
    ReportSeverity,
    ReportStatus,
    UpdateStatusRequest,
)
from app.schemas.notifications import NotifyResidentRequest, NotifyResidentResponse
from app.services.ai_service import AIService
from app.services.duplicate_service import DuplicateService
from app.services.notification_service import NotificationService
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


def get_ai_service() -> AIService:
    return AIService()


def get_duplicate_service() -> DuplicateService:
    return DuplicateService()


def get_notification_service() -> NotificationService:
    return NotificationService()


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    body: CreateReportRequest,
    background_tasks: BackgroundTasks,
    service: ReportService = Depends(get_report_service),
    ai_service: AIService = Depends(get_ai_service),
):
    try:
        report = await service.create_report(body)
        # AI pipeline runs after response is sent — does not block the resident
        background_tasks.add_task(ai_service.run_pipeline, str(report.id))
        return report
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("", response_model=list[ReportDetailResponse])
async def list_reports(
    status: ReportStatus | None = Query(None),
    category: ReportCategory | None = Query(None),
    severity: ReportSeverity | None = Query(None),
    department_id: UUID | None = Query(None),
    bbox: str | None = Query(None, description="minLng,minLat,maxLng,maxLat"),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ReportService = Depends(get_report_service),
):
    try:
        return await service.list_reports(
            status=status,
            category=category,
            severity=severity,
            department_id=department_id,
            bbox=bbox,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# /nearby MUST be defined before /{report_id}
@router.get("/nearby", response_model=list[NearbyReportResponse])
async def list_nearby_reports(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(1.0, gt=0, le=50),
    limit: int = Query(50, ge=1, le=200),
    service: ReportService = Depends(get_report_service),
):
    try:
        return await service.list_nearby_reports(lat=lat, lng=lng, radius_km=radius_km, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
):
    try:
        report = await service.get_report(report_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/duplicates", response_model=list[DuplicateSuggestionResponse])
async def find_report_duplicates(
    report_id: UUID,
    radius_meters: float = Query(500.0, gt=0, le=5000, description="Search radius in meters"),
    similarity_threshold: float = Query(0.35, ge=0.0, le=1.0),
    limit: int = Query(5, ge=1, le=20),
    dup_service: DuplicateService = Depends(get_duplicate_service),
):
    """Run duplicate detection for a report and return candidates for admin review."""
    try:
        return await dup_service.find_duplicates(
            str(report_id),
            radius_meters=radius_meters,
            similarity_threshold=similarity_threshold,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/{report_id}/analyze", response_model=AIAnalysisResponse)
async def analyze_report(
    report_id: UUID,
    ai_service: AIService = Depends(get_ai_service),
):
    """Manually trigger or re-trigger AI analysis for an existing report."""
    try:
        result = await ai_service.analyze_report(str(report_id))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.patch("/{report_id}/status", response_model=ReportDetailResponse)
async def update_report_status(
    report_id: UUID,
    body: UpdateStatusRequest,
    background_tasks: BackgroundTasks,
    service: ReportService = Depends(get_report_service),
    notif_service: NotificationService = Depends(get_notification_service),
):
    try:
        report = await service.update_status(report_id, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    # Notify resident in background — does not block or fail the status update
    background_tasks.add_task(
        notif_service.send_status_update,
        str(report_id),
        body.status.value,
        body.public_note,
    )
    return report


@router.post("/{report_id}/notify", response_model=NotifyResidentResponse)
async def notify_resident(
    report_id: UUID,
    body: NotifyResidentRequest = None,
    notif_service: NotificationService = Depends(get_notification_service),
):
    """Manually send a status notification to the resident."""
    if body is None:
        body = NotifyResidentRequest()
    try:
        results = await notif_service.send_status_update(
            str(report_id),
            new_status=None,  # Fetches current status from DB
            public_note=body.public_note,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return NotifyResidentResponse(results=results, count=len(results))


@router.patch("/{report_id}/department", response_model=ReportDetailResponse)
async def assign_department(
    report_id: UUID,
    body: AssignDepartmentRequest,
    service: ReportService = Depends(get_report_service),
):
    try:
        report = await service.assign_department(report_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
