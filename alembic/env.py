"""
Alembic async env: единственный источник DSN — DATABASE_URL из окружения / .env через config.py.

Строка sqlalchemy.url в alembic.ini намеренно не задаётся: ini-файл не должен дублировать
секреты и не обязан содержать рабочий URL (см. комментарий в alembic.ini).
"""
from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from bot.models.tables import Base
from config import get_settings

config = context.config

target_metadata = Base.metadata


def get_url() -> str:
    """Offline-режим и любые сценарии, где нужен URL без чтения секции ini."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    settings = get_settings()
    # Не используем sqlalchemy.url из alembic.ini — только DATABASE_URL из config.
    configuration = dict(config.get_section(config.config_ini_section) or {})
    configuration["sqlalchemy.url"] = settings.database_url
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
