from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.tables import OrderItem
from bot.repositories.cart_repo import cart_repo
from bot.repositories.order_repo import OrderRepository, order_repo
from bot.repositories.user_repo import user_repo


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._orders: OrderRepository = order_repo(session)
        self._cart = cart_repo(session)
        self._users = user_repo(session)

    async def create_order_from_cart(
        self,
        telegram_id: int,
        payment_provider: str,
        *,
        idempotency_key: str | None = None,
    ) -> int | None:
        user = await self._users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        if idempotency_key:
            existing = await self._orders.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing.id

        rows = await self._cart.list_items_with_products(user.id)
        if not rows:
            return None

        items: list[OrderItem] = []
        total_stars = 0
        total_rub = Decimal("0")
        for row in rows:
            p = row.product
            if p is None:
                continue
            items.append(
                OrderItem(
                    product_id=p.id,
                    product_name=p.name,
                    qty=row.qty,
                    unit_price_rub=p.price_rub,
                    unit_price_stars=p.price_stars,
                )
            )
            total_stars += p.price_stars * row.qty
            if p.price_rub is not None:
                total_rub += p.price_rub * row.qty

        total_rub_out: Decimal | None = total_rub if total_rub > 0 else None
        total_stars_out: int | None = total_stars if total_stars > 0 else None

        order = await self._orders.create_order_from_cart(
            user,
            items,
            payment_provider=payment_provider,
            total_rub=total_rub_out,
            total_stars=total_stars_out,
            idempotency_key=idempotency_key,
        )
        await self._cart.clear(user.id)
        return order.id

    async def get_order(self, order_id: int):
        return await self._orders.get_order(order_id)

    async def mark_paid(
        self,
        order_id: int,
        *,
        telegram_charge_id: str | None = None,
        payment_provider: str | None = None,
    ):
        return await self._orders.mark_paid(
            order_id,
            telegram_charge_id=telegram_charge_id,
            payment_provider=payment_provider,
        )

    async def attach_yookassa_payment(self, order_id: int, payment_id: str) -> None:
        await self._orders.set_yookassa_payment_id(order_id, payment_id)

    async def attach_cryptobot_invoice(self, order_id: int, invoice_id: int) -> None:
        await self._orders.set_cryptobot_invoice_id(order_id, invoice_id)
