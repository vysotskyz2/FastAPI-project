from decimal import Decimal

from sqlalchemy import select, update

from src.infrastructure.models import CurrencyEnum, UserBalance
from src.infrastructure.repositories.base import BaseRepository


class BalanceRepository(BaseRepository):
    async def get_by_user_and_currency(self, user_id: int, currency: str) -> UserBalance | None:
        result = await self._session.execute(
            select(UserBalance).where(
                UserBalance.user_id == user_id,
                UserBalance.currency == currency,
            )
        )
        return result.scalar_one_or_none()

    async def create_default_balances(self, user_id: int) -> None:
        self._session.add_all(
            UserBalance(user_id=user_id, currency=currency.value, amount=0)
            for currency in CurrencyEnum
        )
        await self._session.flush()

    async def add_amount(self, balance_id: int, delta: Decimal) -> Decimal | None:
        stmt = (
            update(UserBalance)
            .where(
                UserBalance.id == balance_id,
                UserBalance.amount + delta >= 0,
            )
            .values(amount=UserBalance.amount + delta)
            .returning(UserBalance.amount)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
