import pytest

from src.application.services import report_service

_SUCCESS_ROWS = [
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


class _FakeAsyncResult:
    def __init__(self, state, result=None):
        self.state = state
        self.result = result


class _FakeTask:
    def delay(self):
        return type("R", (), {"id": "task-123"})()


def _mock(monkeypatch, state, result=None):
    monkeypatch.setattr(report_service, "generate_report", _FakeTask())
    monkeypatch.setattr(
        report_service, "AsyncResult", lambda task_id, app=None: _FakeAsyncResult(state, result)
    )


@pytest.mark.asyncio
async def test_create_report_returns_202(client, monkeypatch):
    _mock(monkeypatch, "PENDING")
    r = await client.post("/reports")
    assert r.status_code == 202
    assert r.json()["task_id"] == "task-123"


@pytest.mark.asyncio
async def test_get_report_success(client, monkeypatch):
    _mock(monkeypatch, "SUCCESS", _SUCCESS_ROWS)
    r = await client.get("/reports/task-123")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "SUCCESS"
    assert len(body["result"]) == 1
    row = body["result"][0]
    assert row["registered_users_count"] == 1
    assert row["transactions_count"] == 1
    assert row["not_rollbacked_transactions_count"] == 0


@pytest.mark.asyncio
async def test_get_report_pending(client, monkeypatch):
    _mock(monkeypatch, "PENDING")
    r = await client.get("/reports/unknown")
    assert r.status_code == 200
    assert r.json()["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_report_failure(client, monkeypatch):
    _mock(monkeypatch, "FAILURE")
    r = await client.get("/reports/failed")
    assert r.status_code == 200
    assert r.json()["status"] == "FAILURE"
