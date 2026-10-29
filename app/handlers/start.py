from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import ClientConfig

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, cfg: ClientConfig):
    rows = []
    if cfg.modules.catalog:
        rows.append([InlineKeyboardButton(text="📖 Каталог", callback_data="catalog")])
    await message.answer(
        cfg.welcome_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )