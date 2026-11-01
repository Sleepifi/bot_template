from aiogram import Router

from . import common
from .catalog import router as catalog_router

router = Router()
router.include_router(common.router)       # /admin, /cancel, меню
router.include_router(catalog_router)      # модуль каталога
router.include_router(common.stub_router)  # заглушка всегда последней