"""
Department service.

Phase 1: Stub implementation. Full database logic is implemented in Phase 3.
"""
from app.schemas.departments import DepartmentResponse


class DepartmentService:
    async def list_departments(self) -> list[DepartmentResponse]:
        # Phase 3: fetch departments from Supabase.
        return []
