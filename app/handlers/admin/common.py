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
        return event.from_user.id in cfg.admins_ids

def admin_router() -> Router:
    r = Router()
    r.message.filter(IsAdmin())
    r.callback_query.filter(IsAdmin())
    return r

def admin_menu(cfg: ClientConfig):
    kb = InlineKeyboardBuilder()

    for key, name, callback in SECTIONS:
        if getattr(cfg.modules,key):
            kb.button(text=name,callback_data=callback)
    kb.adjust(1)
    return kb.as_markup()

router = admin_router()
stub_router = admin_router()

@router.message(Command("admin"))
async def cmd_admin(message: Message, cfg:ClientConfig):
    await message.answer("Панель владельца:", reply_markup=admin_menu(cfg))

@router.callback_query(F.data == "admin:menu")
async def admin_back(call: CallbackQuery, cfg:ClientConfig):
    await call.message.edit_text("Панель владельца:", reply_markup=admin_menu(cfg))
    await call.answer()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, cfg:ClientConfig):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu(cfg))

@stub_router.callback_query(F.data.startswith("admin:"))
async def admin_stub(call: CallbackQuery, cfg:ClientConfig):
    await call.answer("Эта кнопка пока не готова", show_alert=True)