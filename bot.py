#!/usr/bin/env python3
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiohttp import web

from config import BOT_TOKEN
from handlers import start, purchase, admin
from cp_webhook import init_app  # новый файл с обработчиком CloudPayments

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/opt/vpn_bot/bot.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return

    # Бот
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(purchase.router)
    dp.include_router(admin.router)

    # aiohttp-приложение для вебхуков CloudPayments
    app = await init_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8080)
    await site.start()
    logger.info("CloudPayments webhook server started on 127.0.0.1:8080")

    logger.info("Bot started!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
