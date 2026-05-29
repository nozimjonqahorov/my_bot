import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, WEBHOOK_URL, PORT
from db import init_db
from handlers.student import router as student_router
from handlers.teacher import router as teacher_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushurish"),
    ]
    await bot.set_my_commands(commands)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(teacher_router)
    dp.include_router(student_router)

    # Initialize DB
    await init_db()

    # Set bot commands for UI
    await set_commands(bot)

    
    logger.info("Starting long‑polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
