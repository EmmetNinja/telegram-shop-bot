"""
Inline-клавиатуры для админ-панели.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_notification_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отметить выполненным", callback_data=f"complete_order_{order_id}")
    builder.button(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_add_product")
    builder.button(text="📦 Список товаров", callback_data="admin_products")
    builder.button(text="📁 Категории", callback_data="admin_categories")
    builder.button(text="📋 Последние заказы", callback_data="admin_orders")
    builder.button(text="📊 Экспорт в Excel", callback_data="admin_export_excel")
    builder.button(text="◀️ В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def products_list_keyboard(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        status = "🙈 Скрыть" if not p["hidden"] else "👁 Показать"
        builder.button(text=f"{p['name']} [{status}]", callback_data=f"admin_toggle_{p['id']}")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="admin_panel")
    return builder.as_markup()
