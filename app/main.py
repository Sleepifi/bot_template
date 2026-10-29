import asyncio
import os
import logging

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.config import load_config
from app.handlers import catalog, start

from app.db import Database


async def main():
    load_dotenv()
    cfg = load_config()

    name = os.environ["CLIENT"]
    logging.basicConfig(level=logging.INFO)

    db = Database(f"data/{name}.db")   # у каждого клиента своя база
    await db.init(cfg)
    dp["db"] = db

    bot = Bot(token=os.environ["BOT_TOKEN"])
    dp = Dispatcher()
    dp["cfg"] = cfg

    dp.include_router(start.router)
    if cfg.modules.catalog:
        dp.include_router(catalog.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
