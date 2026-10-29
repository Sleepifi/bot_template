from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import ClientConfig

router = Router()


# Короткие префиксы: callback_data в Telegram ограничена 64 байтами
class CategoryCb(CallbackData, prefix="c"):
    id: str


class ProductCb(CallbackData, prefix="p"):
    cat: str
    id: str


@router.callback_query(F.data == "catalog")
async def show_categories(call: CallbackQuery, cfg: ClientConfig):
    kb = InlineKeyboardBuilder()
    for c in cfg.categories:
        kb.button(text=c.title, callback_data=CategoryCb(id=c.id))
    kb.adjust(2)
    await call.message.edit_text("Выберите раздел:", reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(CategoryCb.filter())
async def show_products(call: CallbackQuery, callback_data: CategoryCb, cfg: ClientConfig):
    cat = next(c for c in cfg.categories if c.id == callback_data.id)
    kb = InlineKeyboardBuilder()
    for p in cat.products:
        kb.button(text=f"{p.name} — {p.price} ₽",
                  callback_data=ProductCb(cat=cat.id, id=p.id))
    kb.button(text="⬅️ Назад", callback_data="catalog")
    kb.adjust(1)
    await call.message.edit_text(cat.title, reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(ProductCb.filter())
async def show_product(call: CallbackQuery, callback_data: ProductCb, cfg: ClientConfig):
    cat = next(c for c in cfg.categories if c.id == callback_data.cat)
    p = next(p for p in cat.products if p.id == callback_data.id)
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data=CategoryCb(id=cat.id))
    await call.message.edit_text(
        f"<b>{p.name}</b>\n{p.description}\n\nЦена: {p.price} ₽",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await call.answer()