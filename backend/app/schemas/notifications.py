from pydantic import BaseModel


class NotificationResult(BaseModel):
    """Result of a single notification attempt."""
    channel: str          # "email" | "sms"
    recipient: str        # email address or phone number (masked in logs)
    status: str           # "sent" | "failed" | "skipped"
    is_mock: bool = False # True when provider not configured (no real send)
    error: str | None = None


class NotifyResidentRequest(BaseModel):
    """Optional body for POST /api/reports/{id}/notify."""
    public_note: str | None = None


class NotifyResidentResponse(BaseModel):
    """Returned by notify endpoint — one result per channel attempted."""
    results: list[NotificationResult]
    count: int
