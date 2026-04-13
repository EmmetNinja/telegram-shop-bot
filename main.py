"""
Точка входа: запуск long polling, подключение БД, middleware и роутеров.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from bot.database.db import Database
from bot.handlers import admin, user
from bot.middlewares.auth import AdminMiddleware
from bot.middlewares.db_middleware import DbMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    if not config.BOT_TOKEN:
        logging.error("Задайте BOT_TOKEN в .env или переменных окружения.")
        sys.exit(1)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    db = Database()
    await db.connect()
    await db.init()

    dp = Dispatcher(storage=MemoryStorage())
    # Сначала БД, затем флаг админа — оба доступны в хендлерах
    dp.update.middleware(DbMiddleware(db))
    dp.update.middleware(AdminMiddleware())

    # Админ-роутер раньше пользовательского (пересечение /admin и фильтров)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    logging.info("Бот запущен (long polling).")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
