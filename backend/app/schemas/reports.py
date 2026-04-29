from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ReportSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ReportStatus(str, Enum):
    submitted = "submitted"
    reviewed = "reviewed"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    duplicate = "duplicate"
    rejected = "rejected"


class ReportCategory(str, Enum):
    pothole = "pothole"
    streetlight = "streetlight"
    flooding = "flooding"
    sidewalk_damage = "sidewalk_damage"
    trash_overflow = "trash_overflow"
    damaged_sign = "damaged_sign"
    road_hazard = "road_hazard"
    graffiti = "graffiti"
    snow_or_ice = "snow_or_ice"
    other = "other"


class CreateReportRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str | None = None
    # Single image MVP; stored in report_images table for extensibility
    image_path: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class ReportResponse(BaseModel):
    id: UUID
    status: ReportStatus
    # API field name; maps to public_tracking_token in the database
    tracking_token: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailResponse(BaseModel):
    id: UUID
    description: str
    latitude: float
    longitude: float
    address: str | None
    status: ReportStatus
    category: ReportCategory | None = None
    severity: ReportSeverity | None = None
    department_id: UUID | None = None
    tracking_token: str
    created_at: datetime
    updated_at: datetime
    # AI analysis, images, duplicate candidates, and status history
    # are added in Phase 4 and Phase 5.

    model_config = {"from_attributes": True}


class UpdateStatusRequest(BaseModel):
    status: ReportStatus
    note: str | None = None
    public_note: str | None = None


class AssignDepartmentRequest(BaseModel):
    department_id: UUID
