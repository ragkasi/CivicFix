from fastapi import APIRouter, Depends

from app.schemas.departments import DepartmentResponse
from app.services.department_service import DepartmentService

router = APIRouter()


def get_department_service() -> DepartmentService:
    return DepartmentService()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    service: DepartmentService = Depends(get_department_service),
):
    return await service.list_departments()
