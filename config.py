"""
Конфигурация на pydantic-settings (читает .env и переменные окружения).
"""
from __future__ import annotations

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Bot
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")

    # Database
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="postgresql+asyncpg://user:pass@host:5432/dbname",
    )

    # Redis (FSM)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # YooKassa
    yookassa_shop_id: str = Field(default="", alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str = Field(default="", alias="YOOKASSA_SECRET_KEY")
    yookassa_return_url: str = Field(
        default="https://t.me",
        alias="YOOKASSA_RETURN_URL",
    )

    # Catalog
    catalog_page_size: int = Field(default=5, alias="CATALOG_PAGE_SIZE")

    @property
    def admin_id_set(self) -> set[int]:
        if not self.admin_ids.strip():
            return set()
        out: set[int] = set()
        for part in self.admin_ids.split(","):
            part = part.strip()
            if part and part.isdigit():
                out.add(int(part))
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
