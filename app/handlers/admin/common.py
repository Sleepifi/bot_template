from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import ClientConfig

SECTIONS = [
    ("catalog",  "📖 Каталог",  "admin:catalog"),
    ("delivery", "🚚 Доставка", "admin:delivery"),
]

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, cfg: ClientConfig) -> bool:
        return event.from_user.id in cfg.admin_ids


def admin_router() -> Router:
    r = Router()
    r.message.filter(IsAdmin())
    r.callback_query.filter(IsAdmin())
    return r

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить товар", callback_data="admin:add")
    kb.button(text="✏️ Изменить товар", callback_data="admin:edit")
    kb.button(text="🙈 Скрыть / показать", callback_data="admin:toggle")
    kb.button(text="🗑 Удалить", callback_data="admin:delete")
    kb.adjust(2)
    return kb.as_markup()

router = admin_router()
stub_router = admin_router()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer("Панель владельца:", reply_markup=admin_menu())

@router.callback_query(F.data == "admin:menu")
async def admin_back(call: CallbackQuery):
    await call.message.edit_text("Панель владельца:", reply_markup=admin_menu())
    await call.answer()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())

@stub_router.callback_query(F.data.startswith("admin:"))
async def admin_stub(call: CallbackQuery):
    await call.answer("Эта кнопка пока не готова", show_alert=True)