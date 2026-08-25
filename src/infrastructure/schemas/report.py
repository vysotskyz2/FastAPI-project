from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, field_serializer


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class WeeklyReportRow(BaseModel):
    start_date: date
    end_date: date
    registered_users_count: int
    registered_and_deposit_users_count: int
    registered_and_not_rollbacked_deposit_users_count: int
    not_rollbacked_deposit_amount: Decimal
    not_rollbacked_withdraw_amount: Decimal
    transactions_count: int
    not_rollbacked_transactions_count: int

    @field_serializer("start_date", "end_date")
    def serialize_date(self, value: date) -> str:
        return value.isoformat()

    @field_serializer("not_rollbacked_deposit_amount", "not_rollbacked_withdraw_amount")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)


class ReportRead(BaseModel):
    status: ReportStatus
    result: list[WeeklyReportRow] | None = None


class ReportCreateRead(BaseModel):
    task_id: str
