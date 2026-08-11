from pydantic_settings import BaseSettings

from src.settings.celery import CelerySettings
from src.settings.clickhouse import ClickHouseSettings
from src.settings.db import DatabaseConfig
from src.settings.kafka import KafkaSettings
from src.settings.redis import RedisSettings


class Settings(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()
    kafka: KafkaSettings = KafkaSettings()
    clickhouse: ClickHouseSettings = ClickHouseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()


settings = Settings()
