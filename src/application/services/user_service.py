from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.models import User
from src.infrastructure.models.enums import UserStatusEnum
from src.infrastructure.repositories.balance_repository import BalanceRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.schemas.kafka import UserRegisteredEvent


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        balance_repository: BalanceRepository,
        event_producer: EventProducer | None = None,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._balances = balance_repository
        self._events = event_producer

    @staticmethod
    def normalize_email(email: str) -> str:
        return "".join(email.split()).lower()

    async def register(self, email: str) -> User:
        normalized = self.normalize_email(email)
        if await self._users.get_by_email(normalized):
            raise UserAlreadyExistsError(f"User with email `{normalized}` already exists")
        user = await self._users.create(normalized)
        await self._balances.create_default_balances(user.id)
        await self._session.commit()
        if self._events is not None:
            await self._events.publish_user_registered(
                UserRegisteredEvent(
                    user_id=user.id,
                    email=user.email,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
        return user

    async def update_status(self, user_id: int, new_status: UserStatusEnum) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id `{user_id}` does not exist")
        if user.status == new_status.value:
            if new_status is UserStatusEnum.BLOCKED:
                raise UserAlreadyBlockedError(f"User with id `{user_id}` is already blocked")
            raise UserAlreadyActiveError(f"User with id `{user_id}` is already active")
        updated = await self._users.update_status(user_id, new_status.value)
        await self._session.commit()
        return updated

    async def list_users(
        self,
        user_id: int | None,
        email: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[User]:
        users = await self._users.list_users(user_id, email, status, limit, offset)
        for user in users:
            user.balances.sort(key=lambda balance: balance.amount)
        return users
