"""Department service — Phase 4 real implementation."""
import asyncio

from app.db.supabase import get_supabase_client
from app.schemas.departments import DepartmentResponse


def _run(fn):
    return asyncio.to_thread(fn)


class DepartmentService:
    def _client(self):
        return get_supabase_client()

    async def list_departments(self) -> list[DepartmentResponse]:
        client = self._client()
        result = await _run(
            lambda: client.table("departments")
            .select("*")
            .order("name")
            .execute()
        )
        return [
            DepartmentResponse(
                id=row["id"],
                slug=row["slug"],
                name=row["name"],
                description=row.get("description"),
                contact_email=row.get("contact_email"),
                category_coverage=row.get("category_coverage") or [],
                created_at=row["created_at"],
            )
            for row in result.data
        ]
