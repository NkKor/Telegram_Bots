import asyncio
import logging
import sys
import os
import types
import openai
from datetime import timedelta
import dotenv
from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
import pandas as pd
import requests
import text_info as tinfo
from json import loads, dumps
from hr_bot.util import get_gpt_response
from hr_bot.search import proccess_search_openai

dotenv.load_dotenv()
token = os.getenv('NKKORTOKEN')
ninja_key = os.getenv('NINJA_API_KEY')
openai.api_key = os.getenv('OPENAI_API_KEY')
gpt_model = 'gpt-4o-mini-2024-07-18'
logger = logging.getLogger(__name__)
dp = Dispatcher()

if not os.path.exists("users.csv"):
    users_df = pd.DataFrame(
        columns=[
            'user_id',
            'token_capacity',
            'token_usage',
            'last_message_date',
            'context_capacity',
            'context_usage',
            'context_length',
            'context',
            'chat_id',
            'post_id',
            'post',
            'await_coordinates'
        ]
    )
    users_df.to_csv('users.csv', index=False)

users_df = pd.read_csv("users.csv", index_col='user_id')


@dp.message(CommandStart())
async def start(message: Message):
    global users_df
    user = message.from_user
    if user.id not in users_df.index:
        users_df.loc[user.id] = [2000, 0, message.date, 4000, 0, 0, '[]', message.chat.id, '','', False]
        logger.info(f"Зарегистрировался новый пользователь: {user.id}, добавлена запись в users_df")
    else:
        await message.answer(f"Приветствую тебя, {user.full_name}!")


@dp.message(Command("weather"))
async def weather(message: Message):
    user = message.from_user
    if user.id not in users_df.index:
        await message.answer("Приветствую тебя, {user.full_name}! Тебя нет в базе сотрудников.")
    else:
        await message.answer("Введите свои координаты: lon lat")
        users_df.loc[user.id, 'await_coordinates'] = True


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    if user.id not in users_df.index:
        return await message.answer("Приветствую тебя, {user.full_name}! Тебя нет в базе сотрудников, ты не можешь общаться с ботом.")
    if users_df.loc[user.id, 'token_usage'] >= users_df.loc[user.id, 'token_capacity']:
        return await message.answer('Закончиилсь токены, попробуй написать позже')

    if users_df.loc[user.id, 'await_coordinates']:
        coordinates = message.text.split()
        await message.answer(f'Подожди немного, ищу прогноз погоды...')
        url = 'https://api.open-meteo.com/v1/forecast'
        params = {
            'latitude': coordinates[0],
            'longitude': coordinates[1],
            'current':
                'temperature_2m,'
                'rain,'
                'windspeed_10m,'
                'winddirection_10m,'
                'snowfall',
        }
        weather = requests.get(url, params=params).json()
        weather_data = ' '.join([str(x) + '-' + str(y) for x, y in weather['current'].items()])
        weather_context = [{"role": 'system', "content": f"Интерпретируй в понятный человеку формат данные о погоде и дай рекомендации, что одеть. Данне о погоде:{weather_data}"}]
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=weather_context,
            max_tokens=1000,
            temperature=0.7
        )
        await message.answer(response['choices'][0]['message']['content'])
        users_df.loc[user.id, 'await_coordinates'] = False

    else:
        content = loads(users_df.loc[user.id, 'context']) + [{"role": 'user', "content": message.text}]
        context_len = users_df.loc[user.id, 'context_usage']

        instruction = [{"role": 'system', "content": "Будь полезным ассистентом, давай развернутые, полезные ответы.>"}]
        instruction = instruction + content
        users_df.loc[user.id, 'context'] = dumps(content)
        users_df.loc[user.id, 'context_usage'] = context_len
        await message.answer('Дай подумаю...')
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=instruction,
            max_tokens=1000,
            temperature=0.7
        )
        text_response = response['choices'][0]['message']['content']
        await message.answer(text_response)
        while context_len > users_df.loc[user.id, 'context_capacity']:
            context_len -= len(content[0]['content'])
            content = content[1:]
        users_df.loc[user.id, 'token_usage'] += response['usage']['total_tokens']
        users_df.loc[user.id, 'last_message_date'] = message.date
        users_df.loc[user.id, 'context_length'] += context_len
        users_df.loc[user.id, 'cotext'] = dumps(content)


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")
    finally:
        users_df.to_csv('users.csv')
        logger.info("выполнено сохранение файла users.csv")
