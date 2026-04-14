from aiogram import Router

from bot.handlers import admin, user


def setup_routers() -> Router:
    root = Router()
    root.include_router(admin.router)
    root.include_router(user.router)
    return root
