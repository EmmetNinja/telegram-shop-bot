from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject


class IsAdmin(BaseFilter):
    """True, если пользователь в ADMIN_IDS (см. AdminMiddleware)."""

    async def __call__(self, event: TelegramObject, is_admin: bool) -> bool:
        return is_admin
