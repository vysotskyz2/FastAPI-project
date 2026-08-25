from clickhouse_connect import get_client
from clickhouse_connect.driver.asyncclient import AsyncClient

from src.settings import settings


def create_async_client() -> AsyncClient:
    sync_client = get_client(
        host=settings.clickhouse.host,
        port=settings.clickhouse.http_port,
        username=settings.clickhouse.user,
        password=settings.clickhouse.password,
        database=settings.clickhouse.db,
        interface="http",
        autogenerate_session_id=False,
    )
    return AsyncClient(client=sync_client)
