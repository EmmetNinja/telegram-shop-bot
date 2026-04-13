"""
Конфигурация бота: токен, список администраторов, настройки цен и платежей.
Значения подставляются из переменных окружения или .env (см. python-dotenv).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта (рядом с main.py)
load_dotenv(Path(__file__).resolve().parent / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Список user_id администраторов через запятую: "123,456"
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()
]

# Валюта по умолчанию для отображения цен в каталоге (если заданы оба типа цен)
DEFAULT_PRICE_DISPLAY: str = os.getenv("DEFAULT_PRICE_DISPLAY", "stars")  # stars | rub

# Минимальная сумма заказа в звёздах (Telegram Stars), 0 — без ограничения
MIN_ORDER_STARS: int = int(os.getenv("MIN_ORDER_STARS", "0"))

# Заглушка ЮКасса: в продакшене сюда подставляют shop_id / secret из личного кабинета
YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")


def is_admin(user_id: int) -> bool:
    """Проверка, входит ли пользователь в список администраторов."""
    return user_id in ADMIN_IDS
