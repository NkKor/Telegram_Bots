import asyncio
import logging
import sys
import os
import dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

import pandas as pd
from json import loads, dumps

from sqlalchemy.sql.base import elements

dotenv.load_dotenv()

token = os.getenv('TOKEN')

dp = Dispatcher()

if not os.path.exists("users.csv"):
    users_df = pd.DataFrame(
        columns = [
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

users_df = pd.read_csv("../users.csv", index_col='user_id')


@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    global users_df

    if user.id in users_df.index:
        await message.answer(f'Hi again, {user.first_name}!')
    else:
        users_df.loc[user.id] = [2000, 0, message.date, 4000, 0, '[]']
        await message.answer(f'{user.first_name}, you successfully registered!')



@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    global users_df

    if user.id in users_df.index:
        context = loads(users_df.loc[user.id, 'context'])
        context.append({"role": 'user', "content": message.text})

        context_len = sum([len(element['content']) for element in context])

        while context_len > users_df.loc[user.id, 'context_capacity']:
            context_len -= len(context[0]['content'])
            context = context[1:]

        answer_message = "\n\n".join([element['content'] for element in context])
        await message.answer(answer_message)

        users_df.loc[user.id, 'context'] = dumps(context)
    else:
        await message.answer(f'Register first!')

async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())
    users_df.to_csv('users.csv')
