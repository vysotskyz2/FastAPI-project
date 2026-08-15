from decimal import Decimal

from sqlalchemy import select, update

from src.infrastructure.models import Transaction
from src.infrastructure.models.enums import TransactionStatusEnum
from src.infrastructure.repositories.base import BaseRepository


class TransactionRepository(BaseRepository):
    async def create(self, user_id: int, currency: str, amount: Decimal) -> Transaction:
        transaction = Transaction(user_id=user_id, currency=currency, amount=amount)
        self._session.add(transaction)
        await self._session.flush()
        return transaction

    async def get_by_id(self, transaction_id: int) -> Transaction | None:
        result = await self._session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int | None,
        limit: int,
        offset: int,
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .order_by(Transaction.created.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if user_id is not None:
            stmt = stmt.where(Transaction.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def mark_rollbacked(self, transaction_id: int) -> Transaction | None:
        stmt = (
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(status=TransactionStatusEnum.ROLLBACKED.value)
            .returning(Transaction)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
