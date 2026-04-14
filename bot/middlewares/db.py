from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class DbMiddleware(BaseMiddleware):
    """Пробрасывает async SQLAlchemy session в data['session'] и session_factory."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            async with session.begin():
                data["session"] = session
                data["session_factory"] = self.session_factory
                return await handler(event, data)
