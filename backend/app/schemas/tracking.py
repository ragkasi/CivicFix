from datetime import datetime

from pydantic import BaseModel


class TrackingResponse(BaseModel):
    """Resident-safe view of a report. Never includes private contact info."""
    tracking_token: str
    status: str
    category: str | None = None
    severity: str | None = None
    address: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    public_note: str | None = None
