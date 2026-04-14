from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.tables import Order, OrderItem, OrderStatus, User
from bot.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    async def get_order(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.id == order_id)
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_yookassa_payment_id(self, payment_id: str) -> Order | None:
        stmt = select(Order).where(Order.yookassa_payment_id == payment_id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_cryptobot_invoice_id(self, invoice_id: int) -> Order | None:
        stmt = select(Order).where(Order.cryptobot_invoice_id == invoice_id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Order | None:
        stmt = select(Order).where(Order.idempotency_key == key).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_order_from_cart(
        self,
        user: User,
        items: list[OrderItem],
        *,
        payment_provider: str,
        total_rub: Decimal | None,
        total_stars: int | None,
        idempotency_key: str | None = None,
    ) -> Order:
        order = Order(
            user_id=user.id,
            status=OrderStatus.AWAITING_PAYMENT.value,
            payment_provider=payment_provider,
            total_rub=total_rub,
            total_stars=total_stars,
            idempotency_key=idempotency_key,
        )
        for it in items:
            it.order = order
        self.session.add(order)
        await self.session.flush()
        return order

    async def mark_paid(
        self,
        order_id: int,
        *,
        telegram_charge_id: str | None = None,
        payment_provider: str | None = None,
    ) -> Order | None:
        order = await self.get_order(order_id)
        if order is None:
            return None
        if order.status == OrderStatus.PAID.value:
            return order
        order.status = OrderStatus.PAID.value
        order.paid_at = datetime.now(timezone.utc)
        if telegram_charge_id:
            order.telegram_payment_charge_id = telegram_charge_id
        if payment_provider:
            order.payment_provider = payment_provider
        await self.session.flush()
        return order

    async def set_yookassa_payment_id(self, order_id: int, payment_id: str) -> None:
        order = await self.get_order(order_id)
        if order:
            order.yookassa_payment_id = payment_id
            await self.session.flush()

    async def set_cryptobot_invoice_id(self, order_id: int, invoice_id: int) -> None:
        order = await self.get_order(order_id)
        if order:
            order.cryptobot_invoice_id = invoice_id
            await self.session.flush()

    async def cancel_pending(self, order_id: int) -> None:
        order = await self.get_order(order_id)
        if order and order.status in (
            OrderStatus.PENDING.value,
            OrderStatus.AWAITING_PAYMENT.value,
        ):
            order.status = OrderStatus.CANCELLED.value
            await self.session.flush()

    async def list_orders_for_export(self, limit: int = 5000) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .order_by(Order.id.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())


def order_repo(session: AsyncSession) -> OrderRepository:
    return OrderRepository(session)
