import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db import create_session_factory
from bot.models.tables import Base, Product, User
from bot.services.cart import CartService


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = create_session_factory(engine)
    yield sf
    await engine.dispose()


@pytest.mark.asyncio
async def test_cart_totals(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        async with session.begin():
            u = User(telegram_id=1001, username="u", full_name="U")
            session.add(u)
            await session.flush()
            p = Product(
                name="A",
                description="d",
                price_stars=10,
                price_rub=Decimal("100.00"),
                stock=5,
                is_active=True,
            )
            session.add(p)
            await session.flush()
            from bot.repositories.cart_repo import cart_repo

            await cart_repo(session).add_or_update_qty(u.id, p.id, 2)

    async with session_factory() as session:
        async with session.begin():
            totals = await CartService(session).get_totals(1001)
            assert totals is not None
            assert totals.total_stars == 20
            assert totals.total_rub == Decimal("200")
