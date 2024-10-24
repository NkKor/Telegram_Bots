import asyncio
import logging
import sys
import os
from openai import OpenAI
from bot_v2 import get_geocode
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import pandas as pd
import requests
import tdata as td
from json import loads, dumps

dotenv.load_dotenv()
token = os.getenv('NKKORTOKEN')
ninja_key = os.getenv('NINJA_API_KEY')
client = OpenAI()
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
        await message.answer("Приветствую тебя, {user.full_name}, мы ранее не встречались")
    else:
        builder = ReplyKeyboardBuilder()
        filename = 'city_coordinates.csv'
        if os.path.isfile(filename):
            cities_df = pd.read_csv(filename)
            for index, row in cities_df.iterrows():
                builder.add(KeyboardButton(text=str(row['city'])))

        await message.answer("О погоде в каком из городов земли ты спрашиваешь:",reply_markup=builder.as_markup())
        users_df.loc[user.id, 'await_coordinates'] = True


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    if user.id not in users_df.index:
        await message.answer("Приветствую тебя, {user.full_name}, мы ранее не встречались")
    if users_df.loc[user.id, 'token_usage'] >= users_df.loc[user.id, 'token_capacity']:
        return await message.answer('Закончиилсь токены, попробуй написать позже')

    if users_df.loc[user.id, 'await_coordinates']:
        filename = 'city_coordinates.csv'
        city = message.text
        if os.path.isfile(filename):
            cities_df = pd.read_csv(filename)
            if city in cities_df['city'].values:
                coordinates = cities_df.loc[cities_df['city'] == city, 'longitude'], cities_df.loc[cities_df['city'] == city, 'latitude']
            else:
                coordinates = get_geocode.get_city_geo(city)
                get_geocode.save_city_geo(city, coordinates)
        else:
            coordinates = get_geocode.get_city_geo(city)
            get_geocode.save_city_geo(city, coordinates)

        await message.answer(f'Подожди немного, это того стоит...')
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
        response_context = [
            {"role": 'system', "content": f"{td.personality}"},
            {"role": 'system', "content": f"Интерпретируй в понятный человеку формат данные о погоде и дай в 100 словах рекомендации, что одеть. Данне о погоде:{weather_data}"}]
        response = client.chat.completions.create(
            model=gpt_model,
            messages=response_context,
            max_tokens=1000,
            temperature=0.7
        )
        await message.answer(response['choices'][0]['message']['content'])
        users_df.loc[user.id, 'await_coordinates'] = False

    else:
        content = loads(users_df.loc[user.id, 'context']) + [{"role": 'user', "content": message.text}]
        context_len = users_df.loc[user.id, 'context_usage']

        instruction = [{"role": 'system', "content": f"{td.personality}"}, {"role": 'system', "content": "Будь полезным ассистентом, давай развернутые, полезные ответы.>"}]
        instruction = instruction + content
        users_df.loc[user.id, 'context'] = dumps(content)
        users_df.loc[user.id, 'context_usage'] = context_len
        await message.answer('Дай подумаю...')
        response = client.chat.completions.create(
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
        users_df.loc[user.id, 'context'] = dumps(content)


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
