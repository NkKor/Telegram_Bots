import asyncio
import logging
import sys
import os
import dotenv
import yandex
import pandas as pd
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


dotenv.load_dotenv()
token = os.getenv("TELEGRAM_API_TOKEN")
yandex_iam = os.getenv("YANDEX_TOKEN")
# print(token)
dp = Dispatcher()
try:
    users_list = pd.read_csv("users.csv", index_col= "chat")
except FileNotFoundError:
    users_list = pd.DataFrame(columns=["context"])
    users_list.index.name = "chat"
    users_list.to_csv("users.csv")

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
@dp.message(lambda message: any(word in message.text.strip().lower().split() for word in['exit','"выход"','by','пока']))
async def goodby(message:Message):
    await message.reply(f"Прощай, {message.from_user.first_name}!")
    users_list.to_csv("users.csv")

@dp.message()
async def handle_message(message:Message):
    chat = message.chat.id
    reqest = message.text
    if chat not in users_list.index:
        users_list.loc[chat] = ["[]"]
    context = json.loads(users_list.loc[chat, "context"])
    context.insert(0, {"role": "system", "content": "Отвечай как пират"})
    context.append({"role": "user", "content": reqest})

    """ response = (yandex.ChatCompletion.create(
       # Authorization: Bearer yandex_iam,
        model="gpt-4o-2024-08-06",
        messages=context,
        max_tokens=50,
        temperature=0.7
    ))
    ai_response = response['choices'][0]['message']['content']
    context.append({"role": "assistant", "content": ai_response})
    users_list.at[chat, "context"] = json.dumps(context)
    await message.reply(f"Bot:{ai_response}") """

async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())