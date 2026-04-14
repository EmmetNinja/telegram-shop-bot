"""
Админ-хендлеры: FSM добавления товаров и категорий, отметка заказов.
Доступ: ADMIN_IDS + фильтр IsAdmin.

Рассылка и экспорт в Excel доступны в полной версии (Boosty).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards import admin_kb
from bot.repositories.product_repo import product_repo

router = Router()
router.callback_query.filter(IsAdmin())
router.message.filter(IsAdmin())


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price_stars = State()
    price_rub = State()
    category = State()
    photo = State()


class AddCategory(StatesGroup):
    name = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    cur = await state.get_state()
    if cur:
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb.admin_panel())
    else:
        await message.answer("Нечего отменять.")


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(call: CallbackQuery) -> None:
    await call.message.edit_text("⚙️ <b>Админ-панель</b>", reply_markup=admin_kb.admin_panel())
    await call.answer()


@router.callback_query(F.data.startswith("complete_order_"))
async def cb_complete_order(call: CallbackQuery, session: AsyncSession) -> None:
    from bot.repositories.order_repo import order_repo
    oid = int(call.data.split("_")[2])
    repo = order_repo(session)
    order = await repo.get_order(oid)
    if not order:
        await call.answer("Заказ не найден.", show_alert=True)
        return
    await repo.mark_paid(oid)
    try:
        txt = call.message.text or call.message.caption or ""
        await call.message.edit_text(txt + "\n\n✅ <b>Отмечен оплаченным</b>", reply_markup=None)
    except Exception as e:
        logger.debug("edit complete_order: {}", e)
    await call.answer("Готово.")


# ─── Добавление товара ───────────────────────────────────────

@router.callback_query(F.data == "adm_add_product")
async def adm_add_product_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddProduct.name)
    await call.message.answer("Название товара:")
    await call.answer()


@router.message(StateFilter(AddProduct.name))
async def adm_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.description)
    await message.answer("Описание:")


@router.message(StateFilter(AddProduct.description))
async def adm_product_desc(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProduct.price_stars)
    await message.answer("Цена в Telegram Stars (целое число):")


@router.message(StateFilter(AddProduct.price_stars))
async def adm_product_stars(message: Message, state: FSMContext) -> None:
    try:
        v = int(message.text.strip())
        if v < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите неотрицательное целое число.")
        return
    await state.update_data(price_stars=v)
    await state.set_state(AddProduct.price_rub)
    await message.answer("Цена в рублях (число, 0 — только Stars):")


@router.message(StateFilter(AddProduct.price_rub))
async def adm_product_rub(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw = message.text.strip().replace(",", ".")
    try:
        rub = Decimal(raw) if raw else Decimal("0")
        if rub < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        await message.answer("Введите число, например 199.00 или 0")
        return
    await state.update_data(price_rub=rub if rub > 0 else None)
    cats = await product_repo(session).list_categories_active()
    lines = "\n".join(f"{c.id}. {c.name}" for c in cats) or "(категорий нет)"
    await state.set_state(AddProduct.category)
    await message.answer(f"ID категории или 0 без категории:\n{lines}\n\nОтправьте число:")


@router.message(StateFilter(AddProduct.category))
async def adm_product_category(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        cid = int(message.text.strip())
    except ValueError:
        await message.answer("Число.")
        return
    if cid != 0:
        from bot.models.tables import Category
        c = await session.get(Category, cid)
        if not c:
            await message.answer("Категория не найдена. Введите существующий ID или 0.")
            return
    await state.update_data(category_id=None if cid == 0 else cid)
    await state.set_state(AddProduct.photo)
    await message.answer("Отправьте фото товара или напишите «-» без фото.")


@router.message(StateFilter(AddProduct.photo))
async def adm_product_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        await message.answer("Фото или «-».")
        return
    data = await state.get_data()
    await state.clear()
    pr = product_repo(session)
    try:
        await pr.add_product(
            name=data["name"],
            description=data["description"],
            price_stars=int(data["price_stars"]),
            price_rub=data.get("price_rub"),
            category_id=data.get("category_id"),
            photo_file_id=photo_id,
            stock=999,
        )
        await message.answer("✅ Товар добавлен.", reply_markup=admin_kb.admin_panel())
    except Exception as e:
        logger.exception("add_product: {}", e)
        await message.answer(f"Ошибка: {e}")


# ─── Категория ───────────────────────────────────────────────

@router.callback_query(F.data == "adm_add_category")
async def adm_cat_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddCategory.name)
    await call.message.answer("Название категории:")
    await call.answer()


@router.message(StateFilter(AddCategory.name))
async def adm_cat_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    await state.clear()
    await product_repo(session).add_category(name)
    await message.answer("✅ Категория создана.", reply_markup=admin_kb.admin_panel())
