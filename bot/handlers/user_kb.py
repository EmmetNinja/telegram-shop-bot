"""
Inline-клавиатуры для пользовательской части бота.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=f"📁 {c['name']}", callback_data=f"category_{c['id']}")
    builder.button(text="📦 Без категории", callback_data="category_0")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Каталог", callback_data="catalog")
    builder.button(text="🛒 Корзина", callback_data="cart")
    if is_admin:
        builder.button(text="⚙️ Админ-панель", callback_data="admin_panel")
    builder.adjust(2)
    return builder.as_markup()


def catalog_keyboard(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        label = f"{p['name']} — ⭐{p['price_stars']}"
        if p["price_rub"]:
            label += f" / {p['price_rub']}₽"
        builder.button(text=label, callback_data=f"product_{p['id']}")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ В корзину", callback_data=f"add_cart_{product_id}")
    builder.button(text="◀️ К каталогу", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(items: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"❌ Убрать «{item['name']}»", callback_data=f"remove_cart_{item['product_id']}")
    builder.button(text="⭐ Оплатить Stars", callback_data="checkout_stars")
    builder.button(text="💳 Оплатить ЮКасса", callback_data="checkout_yookassa")
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="◀️ В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="main_menu")
    return builder.as_markup()
