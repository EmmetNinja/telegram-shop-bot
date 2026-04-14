from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.tables import CartItem, User
from bot.repositories.base import BaseRepository


class CartRepository(BaseRepository):
    async def get_user_by_telegram(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_items_with_products(self, user_id: int) -> list[CartItem]:
        stmt = (
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user_id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_or_update_qty(self, user_id: int, product_id: int, delta: int) -> None:
        stmt = select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        )
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        if row is None:
            if delta <= 0:
                return
            self.session.add(
                CartItem(user_id=user_id, product_id=product_id, qty=delta)
            )
        else:
            new_qty = row.qty + delta
            if new_qty <= 0:
                await self.session.delete(row)
            else:
                row.qty = new_qty
        await self.session.flush()

    async def set_qty(self, user_id: int, product_id: int, qty: int) -> None:
        stmt = select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        )
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        if qty <= 0 and row is not None:
            await self.session.delete(row)
        elif qty > 0:
            if row is None:
                self.session.add(
                    CartItem(user_id=user_id, product_id=product_id, qty=qty)
                )
            else:
                row.qty = qty
        await self.session.flush()

    async def clear(self, user_id: int) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id))


def cart_repo(session: AsyncSession) -> CartRepository:
    return CartRepository(session)
