from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.order_repo import order_repo
from config import get_settings


async def notify_admins_new_order(bot: Bot, session: AsyncSession, order_id: int) -> None:
    settings = get_settings()
    if not settings.admin_id_set:
        return
    repo = order_repo(session)
    order = await repo.get_order(order_id)
    if not order or not order.user:
        return
    u = order.user
    buyer = u.username and f"@{u.username}" or u.full_name or f"id{u.telegram_id}"
    lines = "\n".join(f"  • {i.product_name} x{i.qty}" for i in (order.items or []))
    text = (
        f"🛒 <b>Новый заказ #{order_id}</b>\n"
        f"👤 {buyer}\n"
        f"💳 {order.payment_provider}\n"
        f"⭐ {order.total_stars or 0} / {order.total_rub or 0}₽\n\n"
        f"<b>Состав:</b>\n{lines}"
    )
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="✅ Отметить оплачен",
            callback_data=f"complete_order_{order_id}",
        )
    )
    for aid in settings.admin_id_set:
        try:
            await bot.send_message(aid, text, reply_markup=kb.as_markup())
        except Exception as e:
            logger.warning("Admin notify failed {}: {}", aid, e)
