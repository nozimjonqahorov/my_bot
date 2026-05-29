import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import BotCommand, Message
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from config import BOT_TOKEN
from db import init_db
from handlers.student import router as student_router
from handlers.teacher import router as teacher_router
from utils.keyboards import student_start_keyboard, teacher_start_keyboard
from utils.helpers import get_user_role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushurish"),
    ]
    await bot.set_my_commands(commands)

async def health(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server started on port {port}")

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(teacher_router)
    dp.include_router(student_router)

    async def cmd_start(message: Message):
        role = await get_user_role(message.from_user.id)
        if role == 'teacher':
            await message.answer("Assalomu alaykum, ustoz!", reply_markup=teacher_start_keyboard())
        else:
            await message.answer(
                "Assalomu alaykum! Siz talaba sifatida savol yuborishingiz mumkin.",
                reply_markup=student_start_keyboard()
            )

    dp.message.register(cmd_start, Command('start'))

    await init_db()
    await set_commands(bot)

    # Health check server (Render uchun)
    await start_web()

    logger.info("Starting long-polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())