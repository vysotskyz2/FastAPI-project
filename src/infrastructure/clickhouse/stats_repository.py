from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from clickhouse_connect.driver.asyncclient import AsyncClient

from src.infrastructure.schemas.kafka import TransactionEvent, UserRegisteredEvent

_QUERIES_DIR = Path(__file__).parent / "queries"

_USER_EVENTS_COLUMNS = ["user_id", "email", "created"]

_TRANSACTION_EVENTS_COLUMNS = [
    "event_type",
    "transaction_id",
    "user_id",
    "currency",
    "amount",
    "status",
    "created",
]

_WEEKLY_REPORT_SQL = (_QUERIES_DIR / "weekly_report.sql").read_text(encoding="utf-8")


class StatsRepository:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def insert_user_event(self, event: UserRegisteredEvent) -> None:
        await self._client.insert(
            table="user_events",
            data=[[event.user_id, event.email, event.occurred_at]],
            column_names=_USER_EVENTS_COLUMNS,
        )

    async def insert_transaction_event(self, event: TransactionEvent) -> None:
        await self._client.insert(
            table="transaction_events",
            data=[
                [
                    event.event_type.value,
                    event.transaction_id,
                    event.user_id,
                    event.currency,
                    event.amount,
                    event.status,
                    event.occurred_at,
                ]
            ],
            column_names=_TRANSACTION_EVENTS_COLUMNS,
        )

    async def aggregate_weekly(self, weeks: int = 52) -> list[dict]:
        result = await self._client.query(_WEEKLY_REPORT_SQL, parameters={"weeks": weeks})
        rows: list[dict] = []
        for row in result.named_results():
            rows.append(
                {
                    "start_date": row["week"],
                    "end_date": row["week"] + timedelta(days=7),
                    "registered_users_count": row["registered_users_count"] or 0,
                    "registered_and_deposit_users_count": row["registered_and_deposit_users_count"] or 0,
                    "registered_and_not_rollbacked_deposit_users_count": (
                        row["registered_and_not_rollbacked_deposit_users_count"] or 0
                    ),
                    "not_rollbacked_deposit_amount": row["not_rollbacked_deposit_amount"] or Decimal("0"),
                    "not_rollbacked_withdraw_amount": row["not_rollbacked_withdraw_amount"] or Decimal("0"),
                    "transactions_count": row["transactions_count"] or 0,
                    "not_rollbacked_transactions_count": row["not_rollbacked_transactions_count"] or 0,
                }
            )
        return rows
