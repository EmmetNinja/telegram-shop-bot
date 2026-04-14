from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.tables import Category, Product
from bot.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    async def list_categories_active(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.sort_order.asc(), Category.id.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_products_page(
        self,
        *,
        category_id: int | None,
        uncategorized: bool,
        offset: int,
        limit: int,
    ) -> tuple[list[Product], int]:
        conditions = [Product.is_active.is_(True)]
        if uncategorized:
            conditions.append(Product.category_id.is_(None))
        elif category_id is not None and category_id >= 0:
            conditions.append(Product.category_id == category_id)
        count_stmt = select(func.count()).select_from(Product).where(*conditions)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        stmt = (
            select(Product)
            .where(*conditions)
            .order_by(Product.id.asc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all()), total

    async def get_product(self, product_id: int) -> Product | None:
        stmt = select(Product).where(Product.id == product_id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def search_products(self, query: str, limit: int = 20) -> list[Product]:
        q = f"%{query.strip()}%"
        stmt = (
            select(Product)
            .where(
                Product.is_active.is_(True),
                or_(Product.name.ilike(q), Product.description.ilike(q)),
            )
            .order_by(Product.name.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def add_category(self, name: str, sort_order: int = 0) -> Category:
        c = Category(name=name, sort_order=sort_order, is_active=True)
        self.session.add(c)
        await self.session.flush()
        return c

    async def add_product(
        self,
        *,
        name: str,
        description: str,
        price_stars: int,
        price_rub: Decimal | None,
        category_id: int | None,
        photo_file_id: str | None,
        stock: int = 0,
    ) -> Product:
        p = Product(
            name=name,
            description=description,
            price_stars=price_stars,
            price_rub=price_rub,
            category_id=category_id,
            photo_file_id=photo_file_id,
            stock=stock,
            is_active=True,
        )
        self.session.add(p)
        await self.session.flush()
        return p


def product_repo(session: AsyncSession) -> ProductRepository:
    return ProductRepository(session)
