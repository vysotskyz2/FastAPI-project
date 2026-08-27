from src.application.services import report_service
from src.infrastructure.schemas.report import ReportStatus


class FakeAsyncResult:
    def __init__(self, state, result=None):
        self.state = state
        self.result = result


class FakeTask:
    def __init__(self, task_id="abc-123"):
        self._id = task_id

    def delay(self):
        return self

    @property
    def id(self):
        return self._id


def _patch(monkeypatch, state, result=None):
    monkeypatch.setattr(
        report_service, "AsyncResult", lambda task_id, app=None: FakeAsyncResult(state, result)
    )
    return report_service.ReportService()


def test_create_report_returns_task_id(monkeypatch):
    monkeypatch.setattr(report_service, "generate_report", FakeTask("task-xyz"))
    svc = report_service.ReportService()
    assert svc.create_report() == "task-xyz"


def test_get_report_pending(monkeypatch):
    svc = _patch(monkeypatch, "PENDING")
    read = svc.get_report("any")
    assert read.status == ReportStatus.PENDING
    assert read.result is None


def test_get_report_failure(monkeypatch):
    svc = _patch(monkeypatch, "FAILURE", result=ValueError("boom"))
    read = svc.get_report("any")
    assert read.status == ReportStatus.FAILURE
    assert read.result is None


def test_get_report_success(monkeypatch):
    rows = [
        {
            "start_date": "2026-08-24",
            "end_date": "2026-08-31",
            "registered_users_count": 1,
            "registered_and_deposit_users_count": 1,
            "registered_and_not_rollbacked_deposit_users_count": 0,
            "not_rollbacked_deposit_amount": 0.0,
            "not_rollbacked_withdraw_amount": 0.0,
            "transactions_count": 1,
            "not_rollbacked_transactions_count": 0,
        }
    ]
    svc = _patch(monkeypatch, "SUCCESS", result=rows)
    read = svc.get_report("any")
    assert read.status == ReportStatus.SUCCESS
    assert read.result is not None
    assert len(read.result) == 1
    row = read.result[0]
    assert row.registered_users_count == 1
    assert row.transactions_count == 1
    assert row.not_rollbacked_transactions_count == 0
