from clickhouse_connect import get_client

from src.infrastructure.celery.celery_app import celery_app
from src.infrastructure.clickhouse.stats_repository import WEEKLY_REPORT_SQL, map_weekly_rows
from src.infrastructure.schemas.report import WeeklyReportRow
from src.settings import settings


@celery_app.task(name="generate_report")
def generate_report() -> list[dict]:
    client = get_client(
        host=settings.clickhouse.host,
        port=settings.clickhouse.http_port,
        username=settings.clickhouse.user,
        password=settings.clickhouse.password,
        database=settings.clickhouse.db,
        interface="http",
    )
    try:
        result = client.query(WEEKLY_REPORT_SQL, parameters={"weeks": 52})
        rows = map_weekly_rows(result)
    finally:
        client.close()
    return [WeeklyReportRow(**row).model_dump(mode="json") for row in rows]
