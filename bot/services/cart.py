from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.cart_repo import CartRepository, cart_repo
from bot.repositories.user_repo import UserRepository, user_repo


@dataclass
class CartLine:
    product_id: int
    name: str
    qty: int
    price_stars: int
    price_rub: Decimal | None


@dataclass
class CartTotals:
    lines: list[CartLine]
    total_stars: int
    total_rub: Decimal


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cart: CartRepository = cart_repo(session)
        self._users: UserRepository = user_repo(session)

    async def get_totals(self, telegram_id: int) -> CartTotals | None:
        user = await self._users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        rows = await self._cart.list_items_with_products(user.id)
        lines: list[CartLine] = []
        total_stars = 0
        total_rub = Decimal("0")
        for row in rows:
            p = row.product
            if p is None:
                continue
            lines.append(
                CartLine(
                    product_id=p.id,
                    name=p.name,
                    qty=row.qty,
                    price_stars=p.price_stars,
                    price_rub=p.price_rub,
                )
            )
            total_stars += p.price_stars * row.qty
            if p.price_rub is not None:
                total_rub += p.price_rub * row.qty
        return CartTotals(lines=lines, total_stars=total_stars, total_rub=total_rub)

    async def add_product(self, telegram_id: int, product_id: int, delta: int = 1) -> None:
        user = await self._users.upsert_user(telegram_id, None, None)
        await self._cart.add_or_update_qty(user.id, product_id, delta)

    async def clear(self, telegram_id: int) -> None:
        user = await self._users.get_by_telegram_id(telegram_id)
        if user:
            await self._cart.clear(user.id)
