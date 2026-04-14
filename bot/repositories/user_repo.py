from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.tables import User
from bot.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert_user(
        self,
        telegram_id: int,
        username: str | None,
        full_name: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            self.session.add(user)
            await self.session.flush()
            return user
        user.username = username
        user.full_name = full_name
        await self.session.flush()
        return user

    async def iter_telegram_ids(self) -> list[int]:
        stmt = select(User.telegram_id)
        res = await self.session.execute(stmt)
        return [int(x) for x in res.scalars().all()]


def user_repo(session: AsyncSession) -> UserRepository:
    return UserRepository(session)
