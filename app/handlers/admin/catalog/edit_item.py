from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import Database
from app.handlers.admin.common import admin_menu, admin_router

from html import escape

router = admin_router()

PROMPTS = {
    "name": "Введите новое название",
    "price": "Введите новую цену числом",
    "description": "Введите новое описание («-», чтобы очистить)",
}

def edit_card(p):
    status = "виден покупателям" if p["is_available"] else "скрыт"
    text = (
        f"<b>{escape(p['name'])}</b>\n{escape(p['description'])}\n\n"
        f"Цена: {p['price']} ₽\nСтатус: {status}"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Название", callback_data=EditFieldCb(product_id=p["id"], field="name"))
    kb.button(text="💰 Цена", callback_data=EditFieldCb(product_id=p["id"], field="price"))
    kb.button(text="📝 Описание", callback_data=EditFieldCb(product_id=p["id"], field="description"))
    kb.button(text="⬅️ Назад", callback_data=EditCatCb(id=p["category_id"]))
    kb.adjust(1)
    return text, kb.as_markup()

class ChangeItem(StatesGroup):
    new_name = State()
    new_price = State() 
    new_description = State()

class EditProduct(StatesGroup):
    value = State()

class EditCatCb(CallbackData, prefix="ec"):
    id: str

class EditProdCb(CallbackData, prefix="ep"):
    id: int

class EditFieldCb(CallbackData, prefix="ef"):
    product_id: int
    field: str


@router.callback_query(F.data == "admin:edit")
async def edit_start(call: CallbackQuery, db: Database):
    kb = InlineKeyboardBuilder()
    for c in await db.get_categories():
        kb.button(text=c["title"], callback_data=EditCatCb(id=c["id"]))
    kb.button(text="⬅️ Назад", callback_data="admin:catalog")
    kb.adjust(1)
    await call.message.edit_text("В какой категории вы хотите редактировать товар?", reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(EditCatCb.filter())
async def edit_category(call: CallbackQuery, callback_data: EditCatCb, db: Database):
    products = await db.get_products(callback_data.id)
    kb = InlineKeyboardBuilder()
    for p in products:
        mark = "" if p["is_available"] else "🙈 "
        kb.button(text=f"{mark}{p['name']} — {p['price']} ₽", callback_data=EditProdCb(id=p["id"]))
    kb.button(text="⬅️ Назад", callback_data="admin:edit")
    kb.adjust(1)
    text = "Выберите товар:" if products else "В этой категории пока нет товаров."
    await call.message.edit_text(text, reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(EditProdCb.filter())
async def edit_product(call: CallbackQuery, callback_data: EditProdCb, db: Database):
    p = await db.get_product(callback_data.id)
    if p is None:
        await call.answer("Товар не найден", show_alert=True)
        return
    text, markup = edit_card(p)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await call.answer()


@router.callback_query(EditFieldCb.filter())
async def edit_field(call: CallbackQuery, callback_data: EditFieldCb, state: FSMContext):
    await state.update_data(product_id=callback_data.product_id, field=callback_data.field)
    await state.set_state(EditProduct.value)
    await call.message.edit_text(f"{PROMPTS[callback_data.field]} (или /cancel):")
    await call.answer()


@router.message(EditProduct.value, F.text)
async def edit_save(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    field = data["field"]
    text = message.text.strip()

    if field == "price":
        if not text.isdigit():
            await message.answer("Нужно целое число. Попробуйте ещё раз:")
            return
        value = int(text)
    elif field == "description":
        value = "" if text == "-" else text
    else:  # name
        if not text:
            await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
            return
        value = text

    await db.update_product(data["product_id"], field, value)
    await state.clear()

    p = await db.get_product(data["product_id"])
    if p is None:
        await message.answer("Товар не найден.", reply_markup=admin_menu())
        return
    card, markup = edit_card(p)
    await message.answer("✅ Сохранено\n\n" + card, reply_markup=markup, parse_mode="HTML")