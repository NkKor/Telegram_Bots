import asyncio
import logging
import sys
import os
import openai
from datetime import timedelta
import dotenv
from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import pandas as pd
from json import loads, dumps
from hr_bot.util import get_gpt_response
from hr_bot.search import proccess_search_openai


dotenv.load_dotenv()

token = os.getenv('TOKEN')
# openai.api_key = os.getenv("OPENAI_API_KEY")

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
            'context_length',
            'context',
            'chat_id'
        ]
    )
    users_df.to_csv('users.csv', index=False)

users_df = pd.read_csv("users.csv", index_col='user_id')


def main_keybord():
    keybord = [
        [
        KeyboardButton(text='Список вакансий'),
        KeyboardButton(text='Новая вакансия'),
        KeyboardButton(text='Режим чата'),
        ]
    ]
    return keybord


def region_keybord():
    keybord = [
        [
            KeyboardButton(text='Алт. край'),
            KeyboardButton(text='Новосибирск'),
            KeyboardButton(text='Кемерово'),
        ],
        [
            KeyboardButton(text='Павлодар'),
            KeyboardButton(text='Костанай'),
            KeyboardButton(text='Алма-Аты'),
        ],
        [
            KeyboardButton(text='Назад'),
        ]
    ]
    return keybord


@dp.message(CommandStart())
async def start(message: Message):
    global users_df
    main_kb = ReplyKeyboardMarkup(keyboard=main_keybord(), resize_keyboard=True, one_time_keyboard=True)

    user = message.from_user
    await message.answer(str(message.chat.id))
    if user.id in users_df.index:
        await message.answer(f"Рад видеть тебя снова, {user.full_name}\n")
        await message.answer(f"Нажми /help, чтобы узнать мои возможности", reply_markup=main_kb)

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
        await message.answer(f"Я запомнил тебя, {user.full_name}, можешь вернуться к основному меню нажав /start\n")
    else:
        await message.answer(f"Я помню тебя, {user.full_name}, регистрация не требуется\n")


@dp.message(F.text.contains("Список вакансий"))
async def vacancy_list(message: Message):
    region_kb = ReplyKeyboardMarkup(keyboard=region_keybord(), resize_keyboard=True, one_time_keyboard=True)
    await message.answer(f"Выбери регион чтобы просмотреть вакансии", reply_markup=region_kb)


@dp.message(Command("kb_builder"))
async def kb_builder(message: Message):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Кнопка 1"))
    for i in range(10):
        builder.add(KeyboardButton(text=f"Кнопка {i + 1}"))
    builder.adjust(5)
    await message.answer("Клавиатура с кнопками", reply_markup=builder.as_markup(one_time_keyboard=True,resize_keyboard=True))


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    global users_df
    await message.answer('Дай подумаю...')
    if user.id in users_df.index:
        pass
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