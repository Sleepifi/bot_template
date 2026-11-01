from aiogram import Router

from . import add_item, edit_item

router = Router()
router.include_router(add_item.router)
router.include_router(edit_item.router)