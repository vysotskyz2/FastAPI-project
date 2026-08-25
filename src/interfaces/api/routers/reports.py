from fastapi import APIRouter, Depends, Path, status

from src.application.services.report_service import ReportService
from src.infrastructure.schemas import ReportCreateRead, ReportRead
from src.interfaces.api.deps import get_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportCreateRead, status_code=status.HTTP_202_ACCEPTED)
async def create_report(service: ReportService = Depends(get_report_service)) -> ReportCreateRead:
    return ReportCreateRead(task_id=service.create_report())


@router.get("/{task_id}", response_model=ReportRead, status_code=status.HTTP_200_OK)
async def get_report(
    task_id: str = Path(...),
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    return service.get_report(task_id)
