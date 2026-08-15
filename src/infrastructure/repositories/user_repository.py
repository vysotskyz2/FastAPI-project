from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.infrastructure.models import User
from src.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int, *, with_balances: bool = False) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if with_balances:
            stmt = stmt.options(selectinload(User.balances))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str) -> User:
        user = User(email=email)
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_status(self, user_id: int, status: str) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(status=status)
            .returning(User)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        user_id: int | None,
        email: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[User]:
        stmt = (
            select(User)
            .options(selectinload(User.balances))
            .order_by(User.created, User.id)
            .limit(limit)
            .offset(offset)
        )
        if user_id is not None:
            stmt = stmt.where(User.id == user_id)
        if email is not None:
            stmt = stmt.where(User.email == email)
        if status is not None:
            stmt = stmt.where(User.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())
