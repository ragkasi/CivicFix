from datetime import datetime

from pydantic import BaseModel


class TrackingResponse(BaseModel):
    status: str
    category: str | None = None
    created_at: datetime
    public_note: str | None = None
