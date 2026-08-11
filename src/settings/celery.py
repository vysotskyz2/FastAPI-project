from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="celery_",
        env_file=".env",
        extra="ignore",
    )

    broker_url: str
    result_backend: str
