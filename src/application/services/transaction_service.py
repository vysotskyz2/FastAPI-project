from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import (
    BalanceNotFoundError,
    NegativeBalanceError,
    TransactionAlreadyRollbackedError,
    TransactionNotBelongToUserError,
    TransactionNotFoundError,
    UserBlockedError,
    UserNotFoundError,
)
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.models import Transaction
from src.infrastructure.models.enums import TransactionStatusEnum, UserStatusEnum
from src.infrastructure.repositories.balance_repository import BalanceRepository
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.schemas.kafka import TransactionEvent, TransactionEventType


class TransactionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        balance_repository: BalanceRepository,
        transaction_repository: TransactionRepository,
        event_producer: EventProducer | None = None,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._balances = balance_repository
        self._transactions = transaction_repository
        self._events = event_producer

    async def create_transaction(self, user_id: int, currency: str, amount: Decimal) -> Transaction:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id `{user_id}` does not exist")
        if user.status != UserStatusEnum.ACTIVE.value:
            raise UserBlockedError(f"User with id `{user_id}` is blocked")

        balance = await self._balances.get_by_user_and_currency(user_id, currency)
        if balance is None:
            raise BalanceNotFoundError(f"Balance for user `{user_id}` and currency `{currency}` does not exist")

        new_amount = await self._balances.add_amount(balance.id, amount)
        if new_amount is None:
            raise NegativeBalanceError(f"Negative balance for user `{user_id}`")

        transaction = await self._transactions.create(user_id, currency, amount)
        await self._session.commit()
        if self._events is not None:
            await self._events.publish_transaction_event(
                TransactionEvent(
                    event_type=TransactionEventType.CREATED,
                    transaction_id=transaction.id,
                    user_id=user_id,
                    currency=currency,
                    amount=amount,
                    status=transaction.status,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
        return transaction

    async def rollback_transaction(self, user_id: int, transaction_id: int) -> Transaction:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id `{user_id}` does not exist")
        if user.status != UserStatusEnum.ACTIVE.value:
            raise UserBlockedError(f"User with id `{user_id}` is blocked")

        transaction = await self._transactions.get_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError(f"Transaction with id `{transaction_id}` does not exist")
        if transaction.user_id != user_id:
            raise TransactionNotBelongToUserError(
                f"Transaction with id `{transaction_id}` does not belong to user with id `{user_id}`"
            )
        if transaction.status == TransactionStatusEnum.ROLLBACKED.value:
            raise TransactionAlreadyRollbackedError(f"Transaction with id `{transaction_id}` is already rollbacked")

        balance = await self._balances.get_by_user_and_currency(user_id, transaction.currency)
        if balance is None:
            raise BalanceNotFoundError(f"Balance for user `{user_id}` and currency `{transaction.currency}` does not exist")

        delta = abs(transaction.amount) if transaction.amount < 0 else -transaction.amount
        new_amount = await self._balances.add_amount(balance.id, delta)
        if new_amount is None:
            raise NegativeBalanceError(f"Negative balance for user `{user_id}`")

        await self._transactions.mark_rollbacked(transaction_id)
        await self._session.commit()
        if self._events is not None:
            await self._events.publish_transaction_event(
                TransactionEvent(
                    event_type=TransactionEventType.ROLLBACKED,
                    transaction_id=transaction.id,
                    user_id=user_id,
                    currency=transaction.currency,
                    amount=transaction.amount,
                    status=TransactionStatusEnum.ROLLBACKED.value,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
        return transaction

    async def list_transactions(
        self,
        user_id: int | None,
        limit: int,
        offset: int,
    ) -> list[Transaction]:
        return await self._transactions.list_by_user(user_id, limit, offset)
