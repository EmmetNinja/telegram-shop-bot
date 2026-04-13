"""
Админ-хендлеры: добавление товаров (FSM), список товаров, заказы.
Доступно только пользователям из ADMIN_IDS.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.database.db import Database
from bot.keyboards import admin_kb

router = Router()


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price_stars = State()
    price_rub = State()
    photo = State()
    category = State()


class AddCategory(StatesGroup):
    name = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Действие отменено.", reply_markup=admin_kb.admin_panel())
    else:
        await message.answer("Нечего отменять.")


@router.callback_query(F.data.startswith("complete_order_"))
async def cb_complete_order(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    order_id = int(call.data.split("_")[2])
    await db.set_order_paid(order_id)
    try:
        original_text = call.message.text or call.message.caption or ""
        await call.message.edit_text(original_text + "\n\n✅ <b>Заказ отмечен выполненным</b>", reply_markup=None)
    except Exception:
        pass
    await call.answer("✅ Готово!")


@router.callback_query(F.data.startswith("order_details_"))
async def cb_order_details(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    order_id = int(call.data.split("_")[2])
    order = await db.get_order(order_id)
    items = await db.get_order_items(order_id)
    if not order:
        await call.answer("Заказ не найден.", show_alert=True)
        return
    buyer = order["username"] and f"@{order['username']}" or order["full_name"] or f"id{order['user_id']}"
    status_icon = "✅" if order["status"] == "paid" else "⏳"
    items_text = "\n".join(f"  • {i['name']} x{i['qty']} — ⭐{i['price_stars'] * i['qty']}" for i in items)
    text = f"📋 <b>Заказ #{order_id}</b> {status_icon}\n\n👤 Покупатель: {buyer}\n💳 Способ: {order['pay_method']}\n⭐ Итого: {order['total_stars']} Stars"
    if order["total_rub"]:
        text += f" / {order['total_rub']}₽"
    text += f"\n📅 Дата: {order['created_at']}\n\n<b>Состав:</b>\n{items_text}"
    await call.message.answer(text, reply_markup=admin_kb.admin_panel())
    await call.answer()


@router.message(Command("admin"))
async def cmd_admin(message: Message, is_admin: bool) -> None:
    if not is_admin:
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=admin_kb.admin_panel())


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    await call.message.edit_text("⚙️ <b>Админ-панель</b>", reply_markup=admin_kb.admin_panel())
    await call.answer()


@router.callback_query(F.data == "admin_add_product")
async def cb_add_product_start(call: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(AddProduct.name)
    await call.message.edit_text("📝 Введите <b>название</b> товара:", reply_markup=admin_kb.cancel_keyboard())
    await call.answer()


@router.message(AddProduct.name)
async def fsm_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.description)
    await message.answer("📄 Введите <b>описание</b> товара (или «-» чтобы пропустить):", reply_markup=admin_kb.cancel_keyboard())


@router.message(AddProduct.description)
async def fsm_product_desc(message: Message, state: FSMContext) -> None:
    desc = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddProduct.price_stars)
    await message.answer("⭐ Введите цену в <b>Telegram Stars</b> (0 — бесплатно):", reply_markup=admin_kb.cancel_keyboard())


@router.message(AddProduct.price_stars)
async def fsm_product_stars(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("Введите целое число ≥ 0.")
        return
    await state.update_data(price_stars=int(message.text.strip()))
    await state.set_state(AddProduct.price_rub)
    await message.answer("💳 Введите цену в <b>рублях</b> для ЮКасса (0 — если не используется):", reply_markup=admin_kb.cancel_keyboard())


@router.message(AddProduct.price_rub)
async def fsm_product_rub(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("Введите целое число ≥ 0.")
        return
    await state.update_data(price_rub=int(message.text.strip()))
    await state.set_state(AddProduct.photo)
    await message.answer("🖼 Отправьте <b>фото</b> товара или «-» чтобы пропустить:", reply_markup=admin_kb.cancel_keyboard())


@router.message(AddProduct.photo, F.photo)
async def fsm_product_photo(message: Message, state: FSMContext, db: Database) -> None:
    await state.update_data(photo_id=message.photo[-1].file_id)
    await _ask_category(message, state, db)


@router.message(AddProduct.photo, F.text == "-")
async def fsm_product_no_photo(message: Message, state: FSMContext, db: Database) -> None:
    await state.update_data(photo_id="")
    await _ask_category(message, state, db)


async def _ask_category(message: Message, state: FSMContext, db: Database) -> None:
    categories = await db.get_categories()
    await state.set_state(AddProduct.category)
    if not categories:
        await state.update_data(category_id=None)
        await _save_product(message, state, db)
        return
    lines = "\n".join(f"{c['id']}. {c['name']}" for c in categories)
    await message.answer(f"📁 Выберите категорию — введите номер или «0» чтобы пропустить:\n\n{lines}", reply_markup=admin_kb.cancel_keyboard())


@router.message(AddProduct.category)
async def fsm_product_category(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("Введите номер категории или «0».")
        return
    val = int(message.text.strip())
    await state.update_data(category_id=val if val > 0 else None)
    await _save_product(message, state, db)


async def _save_product(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    cur = await db._conn.execute(
        "INSERT INTO products (name, description, price_stars, price_rub, photo_id, category_id) VALUES (?,?,?,?,?,?)",
        (data["name"], data["description"], data["price_stars"], data["price_rub"], data.get("photo_id", ""), data.get("category_id")),
    )
    await db._conn.commit()
    await state.clear()
    await message.answer(f"✅ Товар <b>«{data['name']}»</b> добавлен (ID: {cur.lastrowid}).", reply_markup=admin_kb.admin_panel())


@router.callback_query(F.data == "admin_categories")
async def cb_admin_categories(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    categories = await db.get_categories()
    text = "📁 <b>Категории</b>\n\n"
    text += "\n".join(f"• {c['name']}" for c in categories) if categories else "Категорий пока нет."
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data == "admin_add_category")
async def cb_add_category(call: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(AddCategory.name)
    await call.message.edit_text("📁 Введите название новой категории:", reply_markup=admin_kb.cancel_keyboard())
    await call.answer()


@router.message(AddCategory.name)
async def fsm_category_name(message: Message, state: FSMContext, db: Database) -> None:
    name = message.text.strip()
    await db.add_category(name)
    await state.clear()
    await message.answer(f"✅ Категория <b>«{name}»</b> добавлена.", reply_markup=admin_kb.admin_panel())


@router.callback_query(F.data == "admin_products")
async def cb_admin_products(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    products = await db.get_products(include_hidden=True)
    if not products:
        await call.answer("Товаров пока нет.", show_alert=True)
        return
    await call.message.edit_text("📦 <b>Все товары</b>\n\nНажми на товар чтобы скрыть/показать:", reply_markup=admin_kb.products_list_keyboard(products))
    await call.answer()


@router.callback_query(F.data.startswith("admin_toggle_"))
async def cb_toggle_product(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    product_id = int(call.data.split("_")[2])
    now_hidden = await db.toggle_product_visibility(product_id)
    await call.answer("скрыт 🙈" if now_hidden else "виден 👁")
    products = await db.get_products(include_hidden=True)
    await call.message.edit_reply_markup(reply_markup=admin_kb.products_list_keyboard(products))


@router.callback_query(F.data == "admin_export_excel")
async def cb_export_excel(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    await call.answer("⏳ Формирую файл...")
    from bot.utils.export import build_orders_excel
    from aiogram.types import BufferedInputFile
    from datetime import datetime
    orders, items_by_order = await db.get_all_orders_with_items()
    if not orders:
        await call.message.answer("Заказов пока нет.")
        return
    excel_bytes = build_orders_excel(orders, items_by_order)
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    await call.message.answer_document(BufferedInputFile(excel_bytes, filename=filename), caption=f"📊 Экспорт заказов — {len(orders)} шт.")


@router.callback_query(F.data == "admin_orders")
async def cb_admin_orders(call: CallbackQuery, db: Database, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Нет доступа.", show_alert=True)
        return
    orders = await db.get_recent_orders(limit=15)
    if not orders:
        await call.answer("Заказов пока нет.", show_alert=True)
        return
    lines = []
    for o in orders:
        name = o["full_name"] or f"id{o['user_id']}"
        status_icon = "✅" if o["status"] == "paid" else "⏳"
        line = f"{status_icon} #{o['id']} | {name} | {o['pay_method']} | ⭐{o['total_stars']}"
        if o["total_rub"]:
            line += f"/{o['total_rub']}₽"
        lines.append(line)
    await call.message.edit_text("📋 <b>Последние 15 заказов:</b>\n\n" + "\n".join(lines), reply_markup=admin_kb.admin_panel())
    await call.answer()
