import asyncio
import logging
import sys
import os
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


dotenv.load_dotenv()
token = os.getenv("TELEGRAM_API_TOKEN")
# print(token)
dp = Dispatcher()

class NotNumExeption(Exception):
    def __init__(self, message):
        self.message = ""

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Приветствую тебя, {message.from_user.full_name}\n"
                         f"Вот комманды, доступные тебе:\n"
                         f"/start - запустит\ перезапустит бот\n"
                         f"/get_id - сообщит id текущего чата\n"
                         f"/help - выведет все доступные комманды\n"
                         f"Твой языковой код - {message.from_user.language_code}")


@dp.message(Command("get_id"))
async def get_id(message: Message):
    chat_id = message.chat.id
    await message.answer(str(chat_id))


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(f"""Вот комманды, доступные тебе:\n
                         /start - запустит\ перезапустит бот\n
                         /get_id - сообщит id текущего чата\n
                         /help - выведет все доступные комманды\n""")

# на консультации использован отдельный handler, с более корректной отработкой функции eval
@dp.message(lambda message: any(word in message.text.strip().lower().split() for word in['hi','hello','what’sup']))
async def greet(message:Message):
    await message.reply(f"Hey, {message.from_user.first_name}!")

@dp.message()
async def handle_message(message:Message):
    try:
        if any(char.isalpha() for char in str(message.text)):
            raise NotNumExeption
        await message.reply(f"{message.text} = {eval(message.text)}")
    except Exception:
        await message.reply(f"Привет {message.from_user.full_name},\n"
                            f"'{message.text}' -that’s what you said.""")

async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())