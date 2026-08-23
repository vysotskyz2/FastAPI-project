from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.transaction_service import TransactionService
from src.application.services.user_service import UserService
from src.infrastructure.clickhouse.client import create_async_client
from src.infrastructure.clickhouse.stats_repository import StatsRepository
from src.infrastructure.database import async_session_factory
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.kafka.transaction_consumer import TransactionConsumer
from src.infrastructure.kafka.user_consumer import UserConsumer
from src.infrastructure.repositories.balance_repository import BalanceRepository
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.settings import settings


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.from_dict(settings.model_dump())

    session_factory = providers.Singleton(lambda: async_session_factory)

    event_producer = providers.Singleton(
        EventProducer,
        bootstrap_servers=config.kafka.bootstrap_servers,
        topic_user_events=config.kafka.topic_user_events,
        topic_transaction_events=config.kafka.topic_transaction_events,
    )

    clickhouse_client = providers.Singleton(create_async_client)

    stats_repository = providers.Singleton(
        StatsRepository,
        client=clickhouse_client,
    )

    user_consumer = providers.Singleton(
        UserConsumer,
        topic=config.kafka.topic_user_events,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=config.kafka.group_id,
        stats_repository=stats_repository,
    )

    transaction_consumer = providers.Singleton(
        TransactionConsumer,
        topic=config.kafka.topic_transaction_events,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=config.kafka.group_id,
        stats_repository=stats_repository,
    )

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
        event_producer=event_producer,
    )

    transaction_service = providers.Factory(
        TransactionService,
        session=providers.Dependency(instance_of=AsyncSession),
        user_repository=user_repository,
        balance_repository=balance_repository,
        transaction_repository=transaction_repository,
        event_producer=event_producer,
    )


container = Container()
