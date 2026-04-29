from fastapi import APIRouter, Depends, HTTPException

from app.schemas.tracking import TrackingResponse
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


@router.get("/{tracking_token}", response_model=TrackingResponse)
async def get_tracking_info(
    tracking_token: str,
    service: ReportService = Depends(get_report_service),
):
    try:
        result = await service.get_report_by_tracking_token(tracking_token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return result
