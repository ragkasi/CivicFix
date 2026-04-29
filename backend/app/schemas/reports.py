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


# ─── Nested / embedded schemas ────────────────────────────────────────────────

class DepartmentInfo(BaseModel):
    """Compact department object embedded in report responses."""
    id: UUID
    slug: str
    name: str


class ReportImageResponse(BaseModel):
    id: UUID
    storage_path: str
    public_url: str | None = None
    created_at: datetime


class StatusEventResponse(BaseModel):
    id: UUID
    old_status: str | None = None
    new_status: str
    note: str | None = None
    public_note: str | None = None
    created_at: datetime


# ─── Request schemas ──────────────────────────────────────────────────────────

class CreateReportRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str | None = None
    # Storage path returned by POST /api/upload/image
    image_path: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class UpdateStatusRequest(BaseModel):
    status: ReportStatus
    note: str | None = None
    public_note: str | None = None


class AssignDepartmentRequest(BaseModel):
    department_id: UUID


# ─── Response schemas ─────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    """Returned on successful report creation."""
    id: UUID
    status: ReportStatus
    category: ReportCategory | None = None
    tracking_token: str
    created_at: datetime


class ReportDetailResponse(BaseModel):
    """Full report detail — used for admin views and GET /api/reports/{id}.

    images, status_events, and department are empty/None for list endpoints
    and fully populated for the single-report detail endpoint.
    """
    id: UUID
    description: str
    latitude: float
    longitude: float
    address: str | None = None
    status: ReportStatus
    category: ReportCategory | None = None
    severity: ReportSeverity | None = None
    department_id: UUID | None = None
    department: DepartmentInfo | None = None
    tracking_token: str
    created_at: datetime
    updated_at: datetime
    images: list[ReportImageResponse] = []
    status_events: list[StatusEventResponse] = []
    ai_analysis: None = None  # Phase 5
