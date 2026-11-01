from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.handlers.admin.common import admin_router

router = admin_router()


def catalog_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить товар", callback_data="admin:add")
    kb.button(text="✏️ Редактировать товар", callback_data="admin:edit")
    kb.button(text="🙈 Скрыть / показать", callback_data="admin:toggle")
    kb.button(text="🗑 Удалить товар", callback_data="admin:delete")
    kb.button(text="📁 Добавить категорию", callback_data="admin:add_cat")
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data == "admin:catalog")
async def open_catalog(call: CallbackQuery):
    await call.message.edit_text("📖 Каталог:", reply_markup=catalog_menu())
    await call.answer()