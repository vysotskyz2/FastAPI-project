from datetime import date
from decimal import Decimal

from src.infrastructure.clickhouse.stats_repository import map_weekly_rows


class FakeQueryResult:
    def __init__(self, rows):
        self._rows = rows

    def named_results(self):
        return iter(self._rows)


def test_map_weekly_rows_nulls_become_zeros():
    rows = [
        {
            "week": date(2026, 8, 24),
            "registered_users_count": None,
            "registered_and_deposit_users_count": None,
            "registered_and_not_rollbacked_deposit_users_count": None,
            "not_rollbacked_deposit_amount": None,
            "not_rollbacked_withdraw_amount": None,
            "transactions_count": None,
            "not_rollbacked_transactions_count": None,
        }
    ]
    out = map_weekly_rows(FakeQueryResult(rows))
    assert out == [
        {
            "start_date": date(2026, 8, 24),
            "end_date": date(2026, 8, 31),
            "registered_users_count": 0,
            "registered_and_deposit_users_count": 0,
            "registered_and_not_rollbacked_deposit_users_count": 0,
            "not_rollbacked_deposit_amount": Decimal("0"),
            "not_rollbacked_withdraw_amount": Decimal("0"),
            "transactions_count": 0,
            "not_rollbacked_transactions_count": 0,
        }
    ]


def test_map_weekly_rows_maps_real_values():
    rows = [
        {
            "week": date(2026, 8, 24),
            "registered_users_count": 3,
            "registered_and_deposit_users_count": 2,
            "registered_and_not_rollbacked_deposit_users_count": 1,
            "not_rollbacked_deposit_amount": Decimal("100.5"),
            "not_rollbacked_withdraw_amount": Decimal("-30"),
            "transactions_count": 5,
            "not_rollbacked_transactions_count": 4,
        }
    ]
    out = map_weekly_rows(FakeQueryResult(rows))
    r = out[0]
    assert r["registered_users_count"] == 3
    assert r["registered_and_deposit_users_count"] == 2
    assert r["not_rollbacked_deposit_amount"] == Decimal("100.5")
    assert r["not_rollbacked_withdraw_amount"] == Decimal("-30")
    assert r["transactions_count"] == 5
    assert r["not_rollbacked_transactions_count"] == 4

