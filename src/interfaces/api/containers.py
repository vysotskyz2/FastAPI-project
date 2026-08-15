from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.transaction_service import TransactionService
from src.application.services.user_service import UserService
from src.infrastructure.database import async_session_factory
from src.infrastructure.repositories.balance_repository import BalanceRepository
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.infrastructure.repositories.user_repository import UserRepository


class Container(containers.DeclarativeContainer):
    session_factory = providers.Singleton(lambda: async_session_factory)

    user_repository = providers.Factory(
        UserRepository,
        session=providers.Dependency(instance_of=AsyncSession),
    )
    balance_repository = providers.Factory(
        BalanceRepository,
        session=providers.Dependency(instance_of=AsyncSession),
    )
    transaction_repository = providers.Factory(
        TransactionRepository,
        session=providers.Dependency(instance_of=AsyncSession),
    )

    user_service = providers.Factory(
        UserService,
        session=providers.Dependency(instance_of=AsyncSession),
        user_repository=user_repository,
        balance_repository=balance_repository,
    )

    transaction_service = providers.Factory(
        TransactionService,
        session=providers.Dependency(instance_of=AsyncSession),
        user_repository=user_repository,
        balance_repository=balance_repository,
        transaction_repository=transaction_repository,
    )


container = Container()
