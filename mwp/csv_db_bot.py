import asyncio
import logging
import sys
import os
import openai
from datetime import timedelta
from databases.main import start
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import pandas as pd
from json import loads, dumps
from mwp.util import get_gpt_response
from mwp.search import proccess_search_openai

dotenv.load_dotenv()

token = os.getenv('TOKEN')

dp = Dispatcher()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')

if not os.path.exists("../users.csv"):
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
    global users_df
    user = message.from_user

    await message.answer(str(message.chat.id))
    if user.id in users_df.index:
        await message.answer(f'Hi again, {user.first_name}!')
    else:
        users_df.loc[user.id] = [2000, 0, message.date, 4000, 0, '[]']
        await message.answer(f'{user.first_name}, you successfully registered!')

@dp.message(Command('tokens'))
async def tokens(message: Message):
    global users_df
    user = message.from_user

    if user.id not in users_df.index:
        return await message.answer('You are not registered!')

    if pd.to_datetime(users_df.loc[user.id, 'last_message_date']) + timedelta(minutes=180) > message.date:
        return await message.answer('Try again later!')
    else:
        users_df.loc[user.id, 'token_usage'] = 0
        users_df.loc[user.id, 'last_message_date'] = message.date
        return await message.answer('Токены восстановлены!')


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    global users_df
    await message.answer('Сейчас подумаю...')

    if user.id in users_df.index:
        if users_df.loc[user.id, 'token_usage'] >= users_df.loc[user.id, 'token_capacity']:
            return await message.answer('У вас закончились токены!')

        context = loads(users_df.loc[user.id, 'context'])
        context.append({"role": 'user', "content": message.text})

        context_len = users_df.loc[user.id, 'context_length']


        while context_len > users_df.loc[user.id, 'context_capacity']:
            context_len -= len(context[0]['content'])
            context = context[1:]

        search_res = proccess_search_openai(GOOGLE_API_KEY,
                                            SEARCH_ENGINE_ID,
                                            message.text)
        context.append({"role": 'system', "content": f'Here is information from the internet: {search_res}'})
        gpt_answer = get_gpt_response(context)

        if gpt_answer['msg'] == 'Failed':
            return await message.answer('Что-то пошло не так...')

        response = gpt_answer['response']
        await message.answer(response.choices[0].message["content"])

        context.append({"role": 'user', "content": response.choices[0].message["content"]})
        token_usage = response['usage']['total_tokens']

        users_df.loc[user.id, 'context'] = dumps(context)
        users_df.loc[user.id, 'token_usage'] += token_usage
        users_df.loc[user.id, 'context_length'] += len(response.choices[0].message["content"] + message.text)
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
