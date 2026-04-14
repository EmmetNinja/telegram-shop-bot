import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.models.tables import Base, OrderStatus, PaymentProvider, Product, User
from bot.services.order import OrderService


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from bot.db import create_session_factory

    sf = create_session_factory(engine)
    yield sf
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_order_from_cart(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        async with session.begin():
            u = User(telegram_id=2002, username="x", full_name="X")
            session.add(u)
            await session.flush()
            p = Product(
                name="P",
                description="d",
                price_stars=5,
                price_rub=Decimal("50"),
                stock=1,
                is_active=True,
            )
            session.add(p)
            await session.flush()
            from bot.repositories.cart_repo import cart_repo

            await cart_repo(session).add_or_update_qty(u.id, p.id, 1)

    async with session_factory() as session:
        async with session.begin():
            oid = await OrderService(session).create_order_from_cart(
                2002,
                PaymentProvider.NONE.value,
            )
            assert oid is not None

    async with session_factory() as session:
        async with session.begin():
            order = await OrderService(session).get_order(oid)
            assert order is not None
            assert order.status == OrderStatus.AWAITING_PAYMENT.value
