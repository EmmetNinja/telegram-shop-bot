"""
Утилиты для приёма платежей.
Stars — нативная оплата Telegram.
ЮКасса — заглушка, требует регистрации.
"""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import LabeledPrice

import config


async def send_stars_invoice(
    bot: Bot,
    chat_id: int,
    order_id: int,
    items: list,
) -> None:
    prices = [
        LabeledPrice(
            label=f"{item['name']} x{item['qty']}",
            amount=item["price_stars"] * item["qty"],
        )
        for item in items
    ]
    await bot.send_invoice(
        chat_id=chat_id,
        title="Оплата заказа",
        description=f"Заказ #{order_id} в нашем магазине",
        payload=f"order_{order_id}",
        currency="XTR",
        prices=prices,
        provider_token="",
    )


def get_yookassa_payment_url(order_id: int, amount_rub: int) -> str:
    """
    Заглушка ЮКасса. Для подключения:
    1. Зарегистрируйтесь на yookassa.ru
    2. Получите shop_id и secret_key
    3. Добавьте в .env: YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
    4. Установите: pip install yookassa
    5. Реализуйте создание платежа через API ЮКасса
    """
    if not config.YOOKASSA_SHOP_ID:
        return "⚠️ ЮКасса не настроена. Добавьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env"
    return f"https://yookassa.ru/ (заглушка, заказ #{order_id}, сумма {amount_rub}₽)"
