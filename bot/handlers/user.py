"""
Пользовательские хендлеры: каталог, корзина, оплата Stars + ЮKassa, inline-поиск.
Бизнес-логика в services; здесь только роутинг и ответы Telegram.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import admin_kb, user_kb
from bot.models.tables import PaymentProvider
from bot.notifications import notify_admins_new_order
from bot.repositories.user_repo import user_repo
from bot.services.cart import CartService
from bot.services.catalog import CatalogService
from bot.services.order import OrderService
from bot.services.payment import PaymentService
from config import Settings

router = Router()


async def _edit_text_or_answer(
    call: CallbackQuery, text: str, reply_markup=None
) -> None:
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await call.message.answer(text, reply_markup=reply_markup)


@router.message(Command("admin"))
async def cmd_admin(message: Message, is_admin: bool) -> None:
    if not is_admin:
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=admin_kb.admin_panel())


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, is_admin: bool) -> None:
    u = message.from_user
    await user_repo(session).upsert_user(u.id, u.username, u.full_name)
    await message.answer(
        f"👋 Привет, <b>{u.first_name}</b>!\n\nДобро пожаловать в магазин. Выбери раздел:",
        reply_markup=user_kb.main_menu(is_admin=is_admin),
    )


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, is_admin: bool) -> None:
    await _edit_text_or_answer(call, "Главное меню:", reply_markup=user_kb.main_menu(is_admin=is_admin))
    await call.answer()


@router.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    cat = CatalogService(session, settings)
    categories = await cat.list_categories()
    if not categories:
        products, total, pages = await cat.page_products(all_products=True, page=0)
        if not products:
            await call.answer("Товаров пока нет.", show_alert=True)
            return
        await _edit_text_or_answer(
            call,
            f"🛍 <b>Каталог</b> (всего {total})\nВыбери товар:",
            reply_markup=user_kb.catalog_page_keyboard(
                products, category_id=None, uncategorized=False, all_products=True, page=0, total_pages=pages
            ),
        )
    else:
        await _edit_text_or_answer(
            call,
            "🛍 <b>Каталог</b>\nВыбери категорию:",
            reply_markup=user_kb.categories_keyboard(categories),
        )
    await call.answer()


@router.callback_query(F.data.startswith("category_"))
async def cb_category(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    cid = int(call.data.split("_")[1])
    cat = CatalogService(session, settings)
    if cid == 0:
        products, total, pages = await cat.page_products(uncategorized=True, page=0)
        title = "📦 Без категории"
        uk = user_kb.catalog_page_keyboard(products, category_id=None, uncategorized=True, all_products=False, page=0, total_pages=pages)
    else:
        products, total, pages = await cat.page_products(category_id=cid, page=0)
        title = "🛍 Товары"
        uk = user_kb.catalog_page_keyboard(products, category_id=cid, uncategorized=False, all_products=False, page=0, total_pages=pages)
    if not products:
        await call.answer("Пусто.", show_alert=True)
        return
    await _edit_text_or_answer(call, f"{title}\n(всего {total})\nВыбери товар:", reply_markup=uk)
    await call.answer()


@router.callback_query(F.data.startswith("cat_page_"))
async def cb_cat_page(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    rest = call.data.removeprefix("cat_page_")
    cid_s, page_s = rest.split("_", 1)
    cid, page = int(cid_s), int(page_s)
    cat = CatalogService(session, settings)
    products, total, pages = await cat.page_products(category_id=cid, page=page)
    if not products:
        await call.answer("Пусто.", show_alert=True)
        return
    await _edit_text_or_answer(
        call,
        f"🛍 Товары (всего {total})\nСтр. {page + 1}/{pages}:",
        reply_markup=user_kb.catalog_page_keyboard(products, category_id=cid, uncategorized=False, all_products=False, page=page, total_pages=pages),
    )
    await call.answer()


@router.callback_query(F.data.startswith("uncat_page_"))
async def cb_uncat_page(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    page = int(call.data.split("_")[2])
    cat = CatalogService(session, settings)
    products, total, pages = await cat.page_products(uncategorized=True, page=page)
    if not products:
        await call.answer("Пусто.", show_alert=True)
        return
    await _edit_text_or_answer(
        call,
        f"📦 Без категории (всего {total})\nСтр. {page + 1}/{pages}:",
        reply_markup=user_kb.catalog_page_keyboard(products, category_id=None, uncategorized=True, all_products=False, page=page, total_pages=pages),
    )
    await call.answer()


@router.callback_query(F.data.startswith("all_page_"))
async def cb_all_page(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    page = int(call.data.split("_")[2])
    cat = CatalogService(session, settings)
    products, total, pages = await cat.page_products(all_products=True, page=page)
    if not products:
        await call.answer("Пусто.", show_alert=True)
        return
    await _edit_text_or_answer(
        call,
        f"🛍 Все товары (всего {total})\nСтр. {page + 1}/{pages}:",
        reply_markup=user_kb.catalog_page_keyboard(products, category_id=None, uncategorized=False, all_products=True, page=page, total_pages=pages),
    )
    await call.answer()


@router.callback_query(F.data.startswith("product_"))
async def cb_product(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    pid = int(call.data.split("_")[1])
    p = await CatalogService(session, settings).get_product(pid)
    if not p:
        await call.answer("Не найдено.", show_alert=True)
        return
    text = f"<b>{p.name}</b>\n\n{p.description}\n\n⭐ Stars: <b>{p.price_stars}</b>"
    if p.price_rub is not None:
        text += f"\n💳 RUB: <b>{p.price_rub}</b>"
    if p.stock is not None:
        text += f"\n📦 Остаток: <b>{p.stock}</b>"
    if p.photo_file_id:
        await call.message.delete()
        await call.message.answer_photo(p.photo_file_id, caption=text, reply_markup=user_kb.product_keyboard(p.id))
    else:
        await _edit_text_or_answer(call, text, reply_markup=user_kb.product_keyboard(p.id))
    await call.answer()


@router.callback_query(F.data.startswith("add_cart_"))
async def cb_add_cart(call: CallbackQuery, session: AsyncSession) -> None:
    pid = int(call.data.split("_")[2])
    u = call.from_user
    await user_repo(session).upsert_user(u.id, u.username, u.full_name)
    await CartService(session).add_product(u.id, pid, 1)
    await call.answer("Добавлено в корзину ✅", show_alert=False)


@router.callback_query(F.data == "cart")
async def cb_cart(call: CallbackQuery, session: AsyncSession) -> None:
    totals = await CartService(session).get_totals(call.from_user.id)
    if not totals or not totals.lines:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    lines = "\n".join(
        f"• {x.name} x{x.qty} — ⭐{x.price_stars * x.qty}"
        + (f" / {x.price_rub * x.qty}₽" if x.price_rub else "")
        for x in totals.lines
    )
    text = (
        f"🛒 <b>Корзина</b>\n\n{lines}\n\n"
        f"Итого: ⭐{totals.total_stars}"
        + (f" / {totals.total_rub}₽" if totals.total_rub > 0 else "")
    )
    await _edit_text_or_answer(call, text, reply_markup=user_kb.cart_keyboard())
    await call.answer()


@router.callback_query(F.data == "cart_clear")
async def cb_cart_clear(call: CallbackQuery, session: AsyncSession, is_admin: bool) -> None:
    await CartService(session).clear(call.from_user.id)
    await _edit_text_or_answer(call, "Корзина очищена.", reply_markup=user_kb.main_menu(is_admin=is_admin))
    await call.answer()


@router.callback_query(F.data == "checkout")
async def cb_checkout(call: CallbackQuery, session: AsyncSession) -> None:
    u = call.from_user
    totals = await CartService(session).get_totals(u.id)
    if not totals or not totals.lines:
        await call.answer("Корзина пуста.", show_alert=True)
        return
    order_id = await OrderService(session).create_order_from_cart(u.id, PaymentProvider.NONE.value)
    if not order_id:
        await call.answer("Не удалось оформить.", show_alert=True)
        return
    order = await OrderService(session).get_order(order_id)
    has_rub = bool(order and order.total_rub and order.total_rub > 0)
    has_stars = bool(order and order.total_stars and order.total_stars > 0)
    await _edit_text_or_answer(
        call,
        f"Заказ <b>#{order_id}</b> создан. Выбери способ оплаты:",
        reply_markup=user_kb.payment_keyboard(order_id, has_rub=has_rub, has_stars=has_stars),
    )
    await call.answer()


@router.callback_query(F.data.startswith("pay_stars_"))
async def cb_pay_stars(call: CallbackQuery, session: AsyncSession, settings: Settings, bot) -> None:
    oid = int(call.data.split("_")[2])
    order = await OrderService(session).get_order(oid)
    u = call.from_user
    if not order or not order.user or order.user.telegram_id != u.id:
        await call.answer("Заказ не найден.", show_alert=True)
        return
    if not order.items:
        await call.answer("Пустой заказ.", show_alert=True)
        return
    lines = [{"name": i.product_name, "qty": i.qty, "price_stars": int(i.unit_price_stars or 0)} for i in order.items]
    await PaymentService(settings).send_stars_invoice(bot, u.id, oid, title=f"Заказ #{oid}", lines=lines)
    await call.answer()


@router.callback_query(F.data.startswith("pay_yookassa_"))
async def cb_pay_yookassa(call: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    oid = int(call.data.split("_")[2])
    order = await OrderService(session).get_order(oid)
    u = call.from_user
    if not order or not order.user or order.user.telegram_id != u.id:
        await call.answer("Заказ не найден.", show_alert=True)
        return
    if not order.total_rub or order.total_rub <= 0:
        await call.answer("Нет суммы в рублях.", show_alert=True)
        return
    url, yk_id = await PaymentService(settings).create_yookassa_payment(oid, order.total_rub)
    if not url:
        await call.answer("ЮKassa не настроена. Добавьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env", show_alert=True)
        return
    if yk_id:
        await OrderService(session).attach_yookassa_payment(oid, yk_id)
    await call.message.answer(f"Оплата заказа #{oid}:\n{url}")
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(pre: PreCheckoutQuery, session: AsyncSession) -> None:
    payload = pre.invoice_payload or ""
    if not payload.startswith("order:"):
        await pre.answer(ok=False, error_message="Неверный payload.")
        return
    try:
        oid = int(payload.split(":")[1])
    except (IndexError, ValueError):
        await pre.answer(ok=False, error_message="Неверный заказ.")
        return
    order = await OrderService(session).get_order(oid)
    if not order:
        await pre.answer(ok=False, error_message="Заказ не найден.")
        return
    await pre.answer(ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: Message, session: AsyncSession, bot) -> None:
    sp = message.successful_payment
    payload = sp.invoice_payload or ""
    parts = payload.split(":")
    if len(parts) < 2:
        return
    oid = int(parts[1])
    order = await OrderService(session).get_order(oid)
    if not order:
        return
    await OrderService(session).mark_paid(
        oid,
        telegram_charge_id=sp.telegram_payment_charge_id,
        payment_provider=PaymentProvider.STARS.value,
    )
    await message.answer("✅ Оплата получена. Спасибо!")
    await notify_admins_new_order(bot, session, oid)


@router.inline_query()
async def inline_search(inline_query: InlineQuery, session: AsyncSession, settings: Settings) -> None:
    q = (inline_query.query or "").strip()
    if len(q) < 2:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return
    products = await CatalogService(session, settings).search_inline(q, limit=20)
    results: list[InlineQueryResultArticle] = []
    for p in products:
        rub = f" / {p.price_rub}₽" if p.price_rub else ""
        results.append(
            InlineQueryResultArticle(
                id=str(p.id),
                title=p.name,
                description=f"⭐{p.price_stars}{rub}",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"<b>{p.name}</b>\n{p.description}\n\n"
                        f"⭐ {p.price_stars}{rub}\n\n"
                        f"Откройте бота и добавьте товар из каталога."
                    )
                ),
            )
        )
    await inline_query.answer(results, cache_time=30, is_personal=True)
