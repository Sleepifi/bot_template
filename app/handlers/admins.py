from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from html import escape

from app.config import ClientConfig
from app.db import Database

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, cfg: ClientConfig) -> bool:
        return event.from_user.id in cfg.admins_ids


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

class AddItem(StatesGroup):
    name = State()
    price = State()
    description = State()

class ChangeItem(StatesGroup):
    new_name = State()
    new_price = State() 
    new_description = State()

class AddCatCb(CallbackData, prefix="ac"):
    id: str

class EditProduct(StatesGroup):
    value = State()


class EditCatCb(CallbackData, prefix="ec"):
    id: str


class EditProdCb(CallbackData, prefix="ep"):
    id: int


class EditFieldCb(CallbackData, prefix="ef"):
    product_id: int
    field: str  # "name", "price" или "description"


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

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить товар", callback_data="admin:add")
    kb.button(text="✏️ Изменить товар", callback_data="admin:edit")
    kb.button(text="🙈 Скрыть / показать", callback_data="admin:toggle")
    kb.button(text="🗑 Удалить", callback_data="admin:delete")
    kb.adjust(2)
    return kb.as_markup()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer("Панель владельца:", reply_markup=admin_menu())

@router.callback_query(F.data == "admin:add")
async def add_start(call: CallbackQuery, db: Database):
    await call.answer() 
    kb = InlineKeyboardBuilder()
    for c in await db.get_categories():
        kb.button(text=c["title"], callback_data=AddCatCb(id=c["id"]))
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

@router.callback_query(F.data == "admin:edit")
async def edit_start(call: CallbackQuery, db: Database):
    kb = InlineKeyboardBuilder()
    for c in await db.get_categories():
        kb.button(text=c["title"], callback_data=EditCatCb(id=c["id"]))
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
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

@router.callback_query(F.data.startswith("admin:"))
async def admin_stub(call: CallbackQuery):
    await call.answer("Эта кнопка пока не готова", show_alert=True)