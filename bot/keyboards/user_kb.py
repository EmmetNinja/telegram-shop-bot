from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.models.tables import Category, Product


def main_menu(*, is_admin: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog"))
    b.row(InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"))
    if is_admin:
        b.row(InlineKeyboardButton(text="⚙️ Админка", callback_data="admin_menu"))
    return b.as_markup()


def categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for c in categories:
        b.row(InlineKeyboardButton(text=c.name, callback_data=f"category_{c.id}"))
    b.row(InlineKeyboardButton(text="📦 Без категории", callback_data="category_0"))
    b.row(InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu"))
    return b.as_markup()


def catalog_page_keyboard(
    products: list[Product],
    *,
    category_id: int | None,
    uncategorized: bool,
    all_products: bool = False,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.row(InlineKeyboardButton(text=f"{p.name} — ⭐{p.price_stars}", callback_data=f"product_{p.id}"))
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=_page_cb(category_id, uncategorized, all_products, page - 1)))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=_page_cb(category_id, uncategorized, all_products, page + 1)))
    if nav:
        b.row(*nav)
    b.row(InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="catalog"))
    b.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return b.as_markup()


def _page_cb(category_id: int | None, uncategorized: bool, all_products: bool, page: int) -> str:
    if all_products:
        return f"all_page_{page}"
    if uncategorized:
        return f"uncat_page_{page}"
    return f"cat_page_{category_id}_{page}"


def product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_cart_{product_id}"))
    b.row(InlineKeyboardButton(text="⬅️ К каталогу", callback_data="catalog"))
    return b.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"))
    b.row(InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart_clear"))
    b.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return b.as_markup()


def payment_keyboard(order_id: int, *, has_rub: bool, has_stars: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_stars:
        b.row(InlineKeyboardButton(text="⭐ Telegram Stars", callback_data=f"pay_stars_{order_id}"))
    if has_rub:
        b.row(InlineKeyboardButton(text="💳 ЮKassa (карта)", callback_data=f"pay_yookassa_{order_id}"))
    b.row(InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu"))
    return b.as_markup()


def noop_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="·", callback_data="noop"))
    return b.as_markup()
