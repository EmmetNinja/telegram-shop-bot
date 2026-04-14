from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm_add_product"))
    b.row(InlineKeyboardButton(text="📁 Добавить категорию", callback_data="adm_add_category"))
    b.row(InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu"))
    return b.as_markup()
