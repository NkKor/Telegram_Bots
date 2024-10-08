import asyncio
import logging
import sys
import os
import openai
from datetime import timedelta
import dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import pandas as pd
from json import loads, dumps
from hr_bot.util import get_gpt_response
from hr_bot.search import proccess_search_openai

dotenv.load_dotenv()

token = os.getenv('TOKEN')
logger = logging.getLogger(__name__)
dp = Dispatcher()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')

if not os.path.exists("users.csv"):
    users_df = pd.DataFrame(
        columns=[
            'user_id',
            'token_capacity',
            'token_usage',
            'last_message_date',
            'context_capacity',
            'context_length',
            'context',
            'chat_id'
        ]
    )
    users_df.to_csv('users.csv', index=False)

users_df = pd.read_csv("users.csv", index_col='user_id')


@dp.message(CommandStart())
async def start(message: Message):
    global users_df
    user = message.from_user

    await message.answer(str(message.chat.id))
    if user.id in users_df.index:
        await message.answer(f"Рад видеть тебя снова, {user.full_name}\n")
    else:
        await message.answer(f"Я не знаю тебя, {user.full_name}, сначала нужно зарегистрироваться, нажми /register\n")


@dp.message(Command("register"))
async def register(message: Message):
    """
    Регистрация нового пользователя
    """
    user = message.from_user
    global users_df
    if user.id not in users_df.index:
        users_df.loc[user.id] = [2000, 0, message.date, 4000, 0, '[]', message.chat.id]
        logger.info(f"Зарегистрировался новый пользователь: {user.id}, добавлена запись в users_df")
        await message.answer(f"Я запомнил тебя, {user.full_name}\n")
    else:
        await message.answer(f"Я помню тебя, {user.full_name}, регистрация не требуется\n")


@dp.message(Command("tokens"))
async def tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        await message.answer(f"Осталось токенов: {users_df.loc[user.id,'token_capacity'] - users_df.loc[user.id, 'token_usage']}\n")
    else:
        await message.answer(f"Я не знаю тебя, {user.full_name}, сначала нужно зарегистрироваться, нажми /register\n")


@dp.message(Command("get_tokens"))
async def get_tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id not in users_df.index:
        return await message.answer(f"Я не знаю тебя, {user.full_name}, сначала нужно зарегистрироваться, нажми /register\n")

    if pd.to_datetime(users_df.loc[user.id, 'last_message_date']) + timedelta(minutes=180) > message.date:
        logger.info(f"Пользователь {user.id} слишком часто отправляет запросы на токены")
        return await message.answer('Не так быстро, попробуй ещё раз позже!')
    else:
        users_df.loc[user.id, "token_usage"] = 0
        users_df.loc[user.id, "last_message_date"] = message.date
        logger.info(f"Обновлены токены пользователю: {user.id}")
        await message.answer(f"Токены обновлены, {user.full_name}, доступно: {users_df.loc[user.id, 'token_capacity']}\n")


@dp.message(Command("clear"))
async def clear(message: Message):
    """Фенкция оцистки контекста диалога с ботом"""
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        users_df.loc[user.id, "context"] = '[]'
        logger.info(f"Контекст очищен пользователем: {user.id}")
        await message.answer(f"Контекст успешно очищен, {user.full_name}\n")
    else:
        await message.answer(f"Сначала нужно зарегистрироваться, {user.full_name}, нажми /register\n")


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    global users_df
    await message.answer('Дай подумаю...')

    if user.id in users_df.index:
        if users_df.loc[user.id, 'token_usage'] >= users_df.loc[user.id, 'token_capacity']:
            logger.info("У пользователя закончились токены")
            return await message.answer('Закончиилсь токены, попробуй написать позже')

        context = loads(users_df.loc[user.id, 'context'])
        context.append({"role": 'user', "content": message.text})

        context_len = users_df.loc[user.id, 'context_length']

        while context_len > users_df.loc[user.id, 'context_capacity']:
            context_len -= len(context[0]['content'])
            context = context[1:]

        # Процесс поиска вынесен в отдельный файл search.py
        search_res = proccess_search_openai(GOOGLE_API_KEY,
                                            SEARCH_ENGINE_ID,
                                            message.text)
        context.append({"role": 'system', "content": f'Вот информация из интернета: {search_res}'})
        gpt_answer = get_gpt_response(context)

        if gpt_answer['msg'] == 'Failed':
            logger.debug("Что то пошло не так с запросом к OpenAI в функции get_gpt_response")
            return await message.answer('Что-то пошло не так...')

        response = gpt_answer['response']
        await message.answer(response.choices[0].message["content"])

        context.append({"role": 'user', "content": response.choices[0].message["content"]})
        token_usage = response['usage']['total_tokens']

        users_df.loc[user.id, 'context'] = dumps(context)
        users_df.loc[user.id, 'token_usage'] += token_usage
        users_df.loc[user.id, 'context_length'] += len(response.choices[0].message["content"] + message.text)
    else:
        await message.answer(f"Я не знаю тебя, {user.full_name}, сначала нужно зарегистрироваться, нажми /register\n")


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)
    try:
        for chat in users_df['chat_id']:
            await bot.send_message(chat_id=chat, text="Бот снова работает, Вы можете вернуться к диалогу")
    except Exception as e:
        logger.debug(f"Не удалось отправить сообщения. {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")
    finally:
        users_df.to_csv('users.csv')
        logger.info("выполнено сохранение файла users.csv")

