import asyncio
import logging
import sys
import os
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message


dotenv.load_dotenv()
token = os.getenv("TELEGRAM_API_TOKEN")
# print(token)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message:Message):
    await message.answer(f"Hi {message.from_user.full_name}")

@dp.message()
async def handle_message(message:Message):
    await message.answer(f"Your message {message.text}")

async def main():
    bot = Bot(token = token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())

