from celery.result import AsyncResult

from src.infrastructure.celery.celery_app import celery_app
from src.infrastructure.celery.tasks import generate_report
from src.infrastructure.schemas.report import ReportRead, ReportStatus, WeeklyReportRow

_PENDING_STATES = {"PENDING", "STARTED", "RETRY"}


class ReportService:
    def create_report(self) -> str:
        result = generate_report.delay()
        return result.id

    def get_report(self, task_id: str) -> ReportRead:
        result = AsyncResult(task_id, app=celery_app)
        if result.state in _PENDING_STATES:
            return ReportRead(status=ReportStatus.PENDING)
        if result.state == "SUCCESS":
            rows = [WeeklyReportRow.model_validate(row) for row in result.result]
            return ReportRead(status=ReportStatus.SUCCESS, result=rows)
        return ReportRead(status=ReportStatus.FAILURE)
