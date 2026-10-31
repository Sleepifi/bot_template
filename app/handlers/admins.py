from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import ClientConfig


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, cfg: ClientConfig) -> bool:
        return event.from_user.id in cfg.admin_ids


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить товар", callback_data="admin:add")
    kb.button(text="💰 Изменить цену", callback_data="admin:price")
    kb.button(text="🙈 Скрыть / показать", callback_data="admin:toggle")
    kb.button(text="🗑 Удалить", callback_data="admin:delete")
    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer("Панель владельца:", reply_markup=admin_menu())


@router.callback_query(F.data.startswith("admin:"))
async def admin_stub(call: CallbackQuery):
    await call.answer("Эта кнопка пока не готова", show_alert=True)