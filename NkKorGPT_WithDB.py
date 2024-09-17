import asyncio
import logging
import sys
import os
import openai
import pandas as pd
import json
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


dotenv.load_dotenv()
token = os.getenv("TELEGRAM_API_TOKEN")
dp = Dispatcher()

if not os.path.exists("users.csv"):
    users_df = pd.DataFrame(
        columns=[
            'user_id',
            'token_capacity',
            'token_usage',
            'last_message_date',
            'context_capacity',
            'context_length',
            'context'
        ]
    )
    users_df.to_csv('users.csv', index=False)
users_df = pd.read_csv('users.csv', index_col='user_id')


@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    global users_df
    if user.id not in users_df.index:
        users_df.loc[user.id] = [2000, 0, message.date, 4000, 0, '[]']
        users_df.to_csv('users.csv', index=False)
    else:
        await message.reply("Рады снова тебя видеть, друг")


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


@dp.message()
async def handle_message(message:Message):
    user_id = message.chat.id
    request = message.text
    if user_id not in users_df:
        users_df.loc[user_id] = [2000, 0, message.date, 4000, 0, '[]']
    context = json.loads(users_df.loc[user_id, "context"])
    context.insert(0, {"role": "system", "content": "Отвечай как опытный программист"})
    context.append({"role": "user", "content": request})
    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-08-06",
        messages=context,
        max_tokens=200,
        temperature=0.7
    )
    ai_response = response['choices'][0]['message']['content']
    context.append({"role": "assistant", "content": ai_response})
    users_df.at[user_id, "context"] = json.dumps(context)
    await message.reply(f"Bot:{ai_response}")

async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())