from typing import Any

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = "prod"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "receipts_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = ""
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 2

    _database_url: str = ""

    def model_post_init(self, context: Any, /) -> None:
        self._database_url = PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ).encoded_string()

    @property
    def database_url(self) -> str:
        return self._database_url


config = Config()
