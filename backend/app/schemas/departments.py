from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    contact_email: str | None = None
    category_coverage: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}
