from fastapi import APIRouter, Depends, HTTPException

from app.schemas.departments import DepartmentResponse
from app.services.department_service import DepartmentService

router = APIRouter()


def get_department_service() -> DepartmentService:
    return DepartmentService()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    service: DepartmentService = Depends(get_department_service),
):
    try:
        return await service.list_departments()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
