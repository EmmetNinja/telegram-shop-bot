"""
Пользовательские хендлеры: старт, каталог, корзина, оплата.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards import admin_kb, user_kb
from bot.database.db import Database
from bot.utils.payments import get_yookassa_payment_url, send_stars_invoice

router = Router()


async def _edit_text_or_answer(
    call: CallbackQuery, text: str, reply_markup=None
) -> None:
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await call.message.answer(text, reply_markup=reply_markup)


@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, is_admin: bool) -> None:
    await db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\nДобро пожаловать в наш магазин. Выбери раздел:", reply_markup=user_kb.main_menu(is_admin))


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, is_admin: bool) -> None:
    await _edit_text_or_answer(call, "Главное меню — выбери раздел:", reply_markup=user_kb.main_menu(is_admin))
    await call.answer()


@router.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery, db: Database) -> None:
    categories = await db.get_categories()
    if not categories:
        products = await db.get_products()
        if not products:
            await call.answer("Товаров пока нет 😔", show_alert=True)
            return
        await _edit_text_or_answer(call, "🛍 <b>Каталог товаров</b>\n\nВыбери товар:", reply_markup=user_kb.catalog_keyboard(products))
    else:
        await _edit_text_or_answer(call, "🛍 <b>Каталог</b>\n\nВыбери категорию:", reply_markup=user_kb.categories_keyboard(categories))
    await call.answer()


@router.callback_query(F.data.startswith("category_"))
async def cb_category(call: CallbackQuery, db: Database) -> None:
    category_id = int(call.data.split("_")[1])
    if category_id == 0:
        products = await db.get_products_uncategorized()
        title = "📦 Товары без категории"
    else:
        products = await db.get_products_by_category(category_id)
        title = "🛍 Товары в категории"
    if not products:
        await call.answer("В этой категории пока нет товаров 😔", show_alert=True)
        return
    await _edit_text_or_answer(call, f"{title}\n\nВыбери товар:", reply_markup=user_kb.catalog_keyboard(products))
    await call.answer()


@router.callback_query(F.data.startswith("product_"))
async def cb_product(call: CallbackQuery, db: Database) -> None:
    product_id = int(call.data.split("_")[1])
    p = await db.get_product(product_id)
    if not p:
        await call.answer("Товар не найден.", show_alert=True)
        return
    text = f"<b>{p['name']}</b>\n\n{p['description']}\n\n⭐ Stars: <b>{p['price_stars']}</b>"
    if p["price_rub"]:
        text += f"\n💳 ЮКасса: <b>{p['price_rub']}₽</b>"
    if p["photo_id"]:
        await call.message.delete()
        await call.message.answer_photo(photo=p["photo_id"], caption=text, reply_markup=user_kb.product_keyboard(product_id))
    else:
        await _edit_text_or_answer(call, text, reply_markup=user_kb.product_keyboard(product_id))
    await call.answer()


@router.callback_query(F.data.startswith("add_cart_"))
async def cb_add_cart(call: CallbackQuery, db: Database) -> None:
    product_id = int(call.data.split("_")[2])
    await db.add_to_cart(call.from_user.id, product_id)
    await call.answer("✅ Добавлено в корзину!", show_alert=False)


@router.callback_query(F.data == "cart")
async def cb_cart(call: CallbackQuery, db: Database) -> None:
    items = await db.get_cart(call.from_user.id)
    if not items:
        await call.answer("Корзина пуста 🛒", show_alert=True)
        return
    lines = []
    total_stars = 0
    total_rub = 0
    for item in items:
        lines.append(f"• {item['name']} x{item['qty']} — ⭐{item['price_stars'] * item['qty']}")
        total_stars += item["price_stars"] * item["qty"]
        total_rub += item["price_rub"] * item["qty"]
    text = "🛒 <b>Ваша корзина:</b>\n\n" + "\n".join(lines)
    text += f"\n\n<b>Итого: ⭐{total_stars}"
    if total_rub:
        text += f" / {total_rub}₽"
    text += "</b>"
    await _edit_text_or_answer(call, text, reply_markup=user_kb.cart_keyboard(items))
    await call.answer()


@router.callback_query(F.data.startswith("remove_cart_"))
async def cb_remove_cart(call: CallbackQuery, db: Database) -> None:
    product_id = int(call.data.split("_")[2])
    await db.remove_from_cart(call.from_user.id, product_id)
    items = await db.get_cart(call.from_user.id)
    if not items:
        await _edit_text_or_answer(call, "Корзина пуста 🛒", reply_markup=user_kb.back_to_menu())
        await call.answer("Убрано из корзины")
        return
    await cb_cart(call, db)


@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(call: CallbackQuery, db: Database) -> None:
    await db.clear_cart(call.from_user.id)
    await _edit_text_or_answer(call, "Корзина очищена 🗑", reply_markup=user_kb.back_to_menu())
    await call.answer()


@router.callback_query(F.data == "checkout_stars")
async def cb_checkout_stars(call: CallbackQuery, db: Database) -> None:
    items = await db.get_cart(call.from_user.id)
    if not items:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    order_id = await db.create_order(call.from_user.id, items, pay_method="stars")
    await send_stars_invoice(call.bot, call.from_user.id, order_id, items)
    await call.answer("Инвойс отправлен ⭐")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, db: Database) -> None:
    payload = message.successful_payment.invoice_payload
    order_id = int(payload.split("_")[1])
    await db.set_order_paid(order_id)
    await db.clear_cart(message.from_user.id)
    await message.answer(f"✅ Оплата прошла! Заказ <b>#{order_id}</b> подтверждён.\n\nСпасибо за покупку! 🎉", reply_markup=user_kb.back_to_menu())
    admin_ids = await db.get_admin_ids()
    stars = message.successful_payment.total_amount
    buyer = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    items = await db.get_order_items(order_id)
    items_text = "\n".join(f"  • {i['name']} x{i['qty']} — ⭐{i['price_stars'] * i['qty']}" for i in items)
    notify_text = f"🛒 <b>Новый заказ #{order_id}</b>\n\n👤 {buyer} (id: <code>{message.from_user.id}</code>)\n⭐ Итого: {stars} Stars\n\n<b>Состав:</b>\n{items_text}"
    for admin_id in admin_ids:
        try:
            await message.bot.send_message(admin_id, notify_text, reply_markup=admin_kb.order_notification_kb(order_id))
        except Exception:
            pass


@router.callback_query(F.data == "checkout_yookassa")
async def cb_checkout_yookassa(call: CallbackQuery, db: Database) -> None:
    items = await db.get_cart(call.from_user.id)
    if not items:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    total_rub = sum(i["price_rub"] * i["qty"] for i in items)
    if total_rub == 0:
        await call.answer("У товаров не задана рублёвая цена.", show_alert=True)
        return
    order_id = await db.create_order(call.from_user.id, items, pay_method="yookassa")
    url = get_yookassa_payment_url(order_id, total_rub)
    await call.message.answer(f"💳 Для оплаты заказа <b>#{order_id}</b> перейдите по ссылке:\n\n{url}", reply_markup=user_kb.back_to_menu())
    await call.answer()


from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import hashlib


@router.inline_query()
async def inline_search(query: InlineQuery, db: Database) -> None:
    search = query.query.strip().lower()
    all_products = await db.get_products()
    if search:
        products = [p for p in all_products if search in p["name"].lower()]
    else:
        products = list(all_products[:20])
    results = []
    for p in products[:20]:
        price_text = f"⭐ {p['price_stars']} Stars"
        if p["price_rub"]:
            price_text += f" / {p['price_rub']}₽"
        text = f"<b>{p['name']}</b>\n\n{p['description']}\n\n{price_text}"
        result_id = hashlib.md5(f"{p['id']}".encode()).hexdigest()
        results.append(InlineQueryResultArticle(id=result_id, title=p["name"], description=price_text, input_message_content=InputTextMessageContent(message_text=text, parse_mode="HTML")))
    await query.answer(results, cache_time=30, is_personal=True)
