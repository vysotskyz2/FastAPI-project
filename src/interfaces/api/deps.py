from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.report_service import ReportService
from src.application.services.transaction_service import TransactionService
from src.application.services.user_service import UserService
from src.infrastructure.database import async_session_factory
from src.interfaces.api.containers import container


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return container.user_service(
        session=session,
        user_repository__session=session,
        balance_repository__session=session,
    )


def get_transaction_service(session: AsyncSession = Depends(get_session)) -> TransactionService:
    return container.transaction_service(
        session=session,
        user_repository__session=session,
        balance_repository__session=session,
        transaction_repository__session=session,
    )


def get_report_service() -> ReportService:
    return container.report_service()
