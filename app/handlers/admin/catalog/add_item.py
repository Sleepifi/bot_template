from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import Database
from app.handlers.admin.common import admin_menu, admin_router

router = admin_router()

class AddItem(StatesGroup):
    name = State()
    price = State()
    description = State()

class AddCatCb(CallbackData, prefix="ac"):
    id: str

@router.callback_query(F.data == "admin:add")
async def add_start(call: CallbackQuery, db: Database):
    await call.answer() 
    kb = InlineKeyboardBuilder()
    for c in await db.get_categories():
        kb.button(text=c["title"], callback_data=AddCatCb(id=c["id"]))
    kb.button(text="⬅️ Назад", callback_data="admin:catalog")
    kb.adjust(1)
    await call.message.edit_text("В какую категорию добавить товар?", reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(AddCatCb.filter())
async def add_category(call: CallbackQuery, callback_data: AddCatCb, state: FSMContext):
    await call.answer() 
    await state.update_data(category_id=callback_data.id)
    await state.set_state(AddItem.name)
    await call.message.edit_text("Введите название товара (или /cancel):")
    await call.answer()


@router.message(AddItem.name, F.text)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddItem.price)
    await message.answer("Введите цену числом, например 250:")


@router.message(AddItem.price, F.text)
async def add_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Нужно целое число без букв и пробелов. Попробуйте ещё раз:")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(AddItem.description)
    await message.answer("Введите описание (или «-», если описание не нужно):")


@router.message(AddItem.description, F.text)
async def add_description(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    text = message.text.strip()
    desc = "" if text == "-" else text
    await db.add_product(data["category_id"], data["name"], data["price"], desc)
    await state.clear()
    await message.answer(f"✅ Товар «{data['name']}» добавлен.", reply_markup=admin_menu())
