"""
Точка входа: long polling (PostgreSQL + Redis FSM).
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.db import create_engine, create_session_factory
from bot.handlers import setup_routers
from bot.middlewares import AdminMiddleware, DbMiddleware, SettingsMiddleware
from config import get_settings


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = get_settings()
    if not settings.bot_token:
        logging.error("Задайте BOT_TOKEN в .env")
        sys.exit(1)

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(SettingsMiddleware(settings))
    dp.update.middleware(DbMiddleware(session_factory))
    dp.update.middleware(AdminMiddleware(settings))

    dp.include_router(setup_routers())

    logging.info("Бот запущен (long polling)")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
