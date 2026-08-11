from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="clickhouse_",
        env_file=".env",
        extra="ignore",
    )

    host: str
    http_port: int
    native_port: int
    user: str
    password: str
    db: str

    @property
    def http_url(self) -> str:
        return f"http://{self.host}:{self.http_port}"
