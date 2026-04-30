from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.schemas.geospatial import NearbyReportResponse
from app.schemas.reports import (
    AIAnalysisResponse,
    AssignDepartmentRequest,
    CreateReportRequest,
    ReportCategory,
    ReportDetailResponse,
    ReportResponse,
    ReportSeverity,
    ReportStatus,
    UpdateStatusRequest,
)
from app.services.ai_service import AIService
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


def get_ai_service() -> AIService:
    return AIService()


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
    service: ReportService = Depends(get_report_service),
):
    try:
        report = await service.update_status(report_id, body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


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
