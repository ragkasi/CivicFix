from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.reports import ReportCategory, ReportSeverity, ReportStatus


class NearbyReportResponse(BaseModel):
    """Report returned by the /api/reports/nearby endpoint with distance."""
    id: UUID
    description: str
    category: ReportCategory | None = None
    severity: ReportSeverity | None = None
    status: ReportStatus
    latitude: float
    longitude: float
    address: str | None = None
    department_id: UUID | None = None
    tracking_token: str
    created_at: datetime
    updated_at: datetime
    distance_meters: float


class ReportMapPoint(BaseModel):
    """Lightweight report shape for map pin rendering."""
    id: UUID
    status: ReportStatus
    category: ReportCategory | None = None
    severity: ReportSeverity | None = None
    latitude: float
    longitude: float
    address: str | None = None
