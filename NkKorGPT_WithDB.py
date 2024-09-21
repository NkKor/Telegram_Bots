import asyncio
import logging
import sys
import openai
import os
import pandas as pd
from json import loads, dumps
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


dotenv.load_dotenv()
token = os.getenv("TELEGRAM_API_TOKEN")
openai.api_key = os.getenv("OPENAI_TOKEN")
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
        users_df.loc[user.id] = [500, 0, message.date, 500, 0, '[]']
    else:
        await message.answer(f"Рады снова тебя видеть, {user.full_name}\n")


@dp.message(Command("register"))
async def register(message: Message):
    user = message.from_user
    global users_df
    if user.id not in users_df.index:
        users_df.loc[user.id] = [500, 0, message.date, 500, 0, '[]']
        await message.answer(f"Ты зарегистрирован, {user.full_name}\n")
    else:
        await message.answer(f"Ты уже зарегистрирован, {user.full_name}\n")


@dp.message(Command("clear"))
async def clear(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        users_df.loc[user.id, "context"] = '[]'

        await message.answer(f"Контекст очищен, {user.full_name}\n")
    else:
        await message.answer(f"Ты не зарегистрирован, {user.full_name}, нажми /register\n")


@dp.message(Command("tokens"))
async def tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        await message.answer(f"У тебя осталось {users_df.loc[user.id, 'token_capacity'] - users_df.loc[user.id, 'token_usage']} токенов\n")
    else:
        await message.answer(f"Ты не зарегистрирован, {user.full_name}, нажми /register\n")


@dp.message(Command("get_tokens"))
async def get_tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        users_df.loc[user.id, "token_usage"] = 0
        await message.answer(f"Токены обновлены, {user.full_name}, доступно {users_df.loc[user.id, 'token_capacity']}\n")
    else:
        await message.answer(f"Ты не зарегистрирован, {user.full_name}, нажми /register\n")


@dp.message()
async def handle_message(message:Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:

        context = loads(users_df.loc[user.id, "context"])
        context.append({"role": "user", "content": message.text})
        context_len = sum([len(element["content"]) for element in context])

        if context_len > users_df.loc[user.id, "context_capacity"]:
            await message.answer("Контекст переполнен, необходимо очистить, чтобы продолжить диалог нажмите /clear")
        #elif message.date - users_df.loc[user.id, "last_message_date"] < 120:
        #   print("Слишком маленький интервал между сообщениями")
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4o-2024-08-06",
                messages=context,
                max_tokens=100,
                temperature=0.7
            )
            ai_response = response["choices"][0]["message"]["content"]
            context.append({"role": "assistant", "content": ai_response})
            users_df.loc[user.id, "token_usage"] += response["usage"]["total_tokens"]
            users_df.loc[user.id, "last_message_date"] = message.date
            await message.answer(ai_response)

       # answer_message = "\n".join([element["content"] for element in context])
        users_df.loc[user.id, "context"] = dumps(context)
        users_df.to_csv("users.csv")
    else:
        await message.answer(f"Сначала нужно зарегистрироваться, {user.full_name}, нажмите /register\n")


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())
