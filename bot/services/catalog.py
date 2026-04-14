from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.product_repo import ProductRepository, product_repo
from config import Settings


class CatalogService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._products = product_repo(session)

    async def list_categories(self):
        return await self._products.list_categories_active()

    async def page_products(
        self,
        *,
        category_id: int | None = None,
        uncategorized: bool = False,
        all_products: bool = False,
        page: int = 0,
    ) -> tuple[list, int, int]:
        page = max(0, page)
        limit = max(1, self._settings.catalog_page_size)
        offset = page * limit
        if all_products:
            cid, unc = None, False
        elif uncategorized:
            cid, unc = None, True
        else:
            cid, unc = category_id, False
        items, total = await self._products.list_products_page(
            category_id=cid,
            uncategorized=unc,
            offset=offset,
            limit=limit,
        )
        pages = max(1, (total + limit - 1) // limit)
        return items, total, pages

    async def get_product(self, product_id: int):
        return await self._products.get_product(product_id)

    async def search_inline(self, query: str, limit: int = 20):
        return await self._products.search_products(query, limit=limit)
