"""
Платёжный сервис: Telegram Stars и ЮKassa.

CryptoBot и Webhook-режим доступны в полной версии (Boosty).
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from aiogram import Bot
from aiogram.types import LabeledPrice

from bot.models.tables import PaymentProvider
from config import Settings


class PaymentService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _yookassa_configured(self) -> bool:
        return bool(self._settings.yookassa_shop_id and self._settings.yookassa_secret_key)

    async def send_stars_invoice(
        self,
        bot: Bot,
        chat_id: int,
        order_id: int,
        title: str,
        lines: list[dict[str, Any]],
    ) -> None:
        """Отправляет инвойс Telegram Stars."""
        prices = [
            LabeledPrice(
                label=f"{x['name']} x{x['qty']}",
                amount=int(x["price_stars"]) * int(x["qty"]),
            )
            for x in lines
        ]
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=f"Заказ #{order_id}",
            payload=f"order:{order_id}:{PaymentProvider.STARS.value}",
            currency="XTR",
            prices=prices,
            provider_token="",
        )

    async def create_yookassa_payment(
        self,
        order_id: int,
        amount_rub: Decimal,
        return_url: str | None = None,
    ) -> tuple[str | None, str | None]:
        """
        Создаёт платёж ЮKassa и возвращает (url, payment_id).
        Требует YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env.
        """
        if not self._yookassa_configured():
            return None, None
        try:
            from yookassa import Configuration, Payment  # type: ignore
        except ImportError:
            return None, None

        Configuration.account_id = self._settings.yookassa_shop_id
        Configuration.secret_key = self._settings.yookassa_secret_key

        def _sync_create() -> Any:
            return Payment.create(
                {
                    "amount": {
                        "value": str(amount_rub.quantize(Decimal("0.01"))),
                        "currency": "RUB",
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": return_url or self._settings.yookassa_return_url,
                    },
                    "capture": True,
                    "description": f"Заказ #{order_id}",
                    "metadata": {"order_id": str(order_id)},
                }
            )

        payment = await asyncio.to_thread(_sync_create)
        url = getattr(payment.confirmation, "confirmation_url", None)
        pid = getattr(payment, "id", None)
        return url, str(pid) if pid else None
