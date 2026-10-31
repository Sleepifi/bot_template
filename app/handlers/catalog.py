from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import Database

router = Router()


class CategoryCb(CallbackData, prefix="c"):
    id: str


class ProductCb(CallbackData, prefix="p"):
    id: int

class PaymentCb(CallbackData, prefix="m"):
    amount:int

@router.callback_query(F.data == "catalog")
async def show_categories(call: CallbackQuery, db: Database):
    kb = InlineKeyboardBuilder()
    for c in await db.get_categories():
        kb.button(text=c["title"], callback_data=CategoryCb(id=c["id"]))
    kb.adjust(1)
    await call.message.edit_text("Выберите раздел:", reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(CategoryCb.filter())
async def show_products(call: CallbackQuery, callback_data: CategoryCb, db: Database):
    cat = await db.get_category(callback_data.id)
    products = await db.get_products(callback_data.id)
    kb = InlineKeyboardBuilder()
    for p in products:
        kb.button(text=f"{p['name']} — {p['price']} ₽", callback_data=ProductCb(id=p["id"]))
    kb.button(text="⬅️ Назад", callback_data="catalog")
    kb.adjust(1)
    title = cat["title"] if products else f"{cat['title']}\n\nПока здесь пусто"
    await call.message.edit_text(title, reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(ProductCb.filter())
async def show_product(call: CallbackQuery, callback_data: ProductCb, db: Database):
    p = await db.get_product(callback_data.id)
    if p is None:
        await call.answer("Товар не найден", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data=CategoryCb(id=p["category_id"]))
    kb.button(text="Оплата", callback_data=PaymentCb(amount=p["price"]))
    kb.adjust(2)
    await call.message.edit_text(
        f"<b>{p['name']}</b>\n{p['description']}\n\nЦена: {p['price']} ₽",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await call.answer()
@router.callback_query(PaymentCb.filter())
async def show_product(call: CallbackQuery, callback_data: PaymentCb, db: Database):
    await call.answer(str(callback_data.amount))