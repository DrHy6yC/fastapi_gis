from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Настройка среды
    MODE: Literal["TEST", "LOCAL", "DEV", "PROD"] = Field(default="LOCAL")
    DB_HOST: str = Field(default="")

    # Настройки БД
    PG_HOST: str = Field(default="")
    PG_PORT: int = Field(default=0)
    PG_USER: str = Field(default="")
    PG_PASSWORD: str = Field(default="")
    PG_DB_NAME: str = Field(default="")
    PG_DATA: str = Field(default="")

    # Настройки сервера
    HOST: str = Field(default="")

    @property
    def db_url(self) -> str:
        """
        Возвращает строку подключения к БД
        :return: str
        """
        return (
            f"postgresql+asyncpg:"
            f"//{self.PG_USER}:{self.PG_PASSWORD}@"
            f"{self.DB_HOST}:{self.PG_PORT}/{self.PG_DB_NAME}"
        )

    # Настройки откуда будут браться данные переменных окружения
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
