from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import Settings


class AdminMiddleware(BaseMiddleware):
    """Добавляет data['is_admin'] по списку ADMIN_IDS."""

    def __init__(self, settings: Settings) -> None:
        self._admin_ids = settings.admin_id_set

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        uid = int(user.id) if user else 0
        data["is_admin"] = uid in self._admin_ids
        return await handler(event, data)
