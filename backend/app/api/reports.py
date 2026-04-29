from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

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
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    body: CreateReportRequest,
    service: ReportService = Depends(get_report_service),
):
    try:
        return await service.create_report(body)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("", response_model=list[ReportDetailResponse])
async def list_reports(
    status: ReportStatus | None = Query(None),
    category: ReportCategory | None = Query(None),
    severity: ReportSeverity | None = Query(None),
    department_id: UUID | None = Query(None),
    bbox: str | None = Query(None, description="minLng,minLat,maxLng,maxLat"),
    limit: int = Query(50, ge=1, le=200),
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


@router.patch("/{report_id}/status", response_model=ReportDetailResponse)
async def update_report_status(
    report_id: UUID,
    body: UpdateStatusRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.update_status(report_id, body)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}/department", response_model=ReportDetailResponse)
async def assign_department(
    report_id: UUID,
    body: AssignDepartmentRequest,
    service: ReportService = Depends(get_report_service),
):
    report = await service.assign_department(report_id, body)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
