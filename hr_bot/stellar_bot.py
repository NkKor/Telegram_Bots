import asyncio
import logging
import sys
import os
import openai
from datetime import timedelta
import dotenv
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
import pandas as pd
import tdata as td
from json import loads, dumps
from hr_bot.util import get_gpt_response
from hr_bot.search import proccess_search_openai


dotenv.load_dotenv()
token = os.getenv('TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = logging.getLogger(__name__)
dp = Dispatcher()
post_dict = td.posts
post_learn_links = td.post_learn_links

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


def main_keyboard():
    keybord = [
        [
            KeyboardButton(text='Видео о компании'),
            KeyboardButton(text='Информация о компании'),
        ],[
            KeyboardButton(text='Правила трудового распорядка'),
            KeyboardButton(text='Должностные инструкции'),
        ],[
            KeyboardButton(text='Схема работы служебного транспорта'),
        ],[
            KeyboardButton(text='Правила пользования кухней и душевой'),
        ],[

        ],
    ]
    return keybord


def instructions_keybord(message):
    """Функция формирующая динамческую клавиатуру из списка
    ссылок, предоставляя документы только в соответствии с должностью пользователя.
    :param message - текущее сообщение пользователя, по нему определяется id и соответственно должность пользователя
    post_learn_links Список ссылок на должностные инструкции хранится в файле tdata.py
    :return: keyboard - type(list) - список кнопок с инструкциями
    """
    global users_df
    global post_learn_links
    current_user_post = []
    user = message.from_user
    try:
        current_user_post = users_df.loc[user.id,'post_id']
    except Exception as e:
        logger.info("Провал с запросом списка инструкций!!!")

    link_list = post_learn_links.get(current_user_post)
    keyboard = []
    try:
        for n, link in enumerate(link_list):
            keyboard.append([InlineKeyboardButton(text=f'Инструкция # {n}', url=link)])
    except Exception as e:
        logger.info("Провал с формированием списка должностных инструкций!!!")
    return keyboard


def video_keybord():
    keybord = [
        [
            InlineKeyboardButton(text="Лого", callback_data="about_company"),
            InlineKeyboardButton(text="Наша продукция", callback_data="our_product_1"),
        ],[
            InlineKeyboardButton(text="Наша продукция2", callback_data="our_product_2"),
            InlineKeyboardButton(text="Наша продукция3", callback_data="our_product_3"),
        ],[
            InlineKeyboardButton(text="Наша продукция4", callback_data="our_product_4"),
        ],
    ]
    return keybord


@dp.message(CommandStart())
async def start(message: types.Message):
    global users_df
    main_kb = ReplyKeyboardMarkup(keyboard=main_keyboard(), resize_keyboard=True, one_time_keyboard=True)

    user = message.from_user
    if user.id in users_df.index:
        await message.answer(f"Рад видеть тебя снова, {user.full_name}\n"
                             f"Выбери то, что тебя интересует в меню ниже", reply_markup=main_kb)
        await message.answer(f"Нажми /help, если нужна помощь")

    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников.\n")
        await message.answer(f"Введи ниже код должности, переданный сотрудником HR департамента:\n")


@dp.message(F.text.contains("Информация о компании"))
async def video(message: Message):
    youtube_link = [[InlineKeyboardButton(text="Видео о компании на Youtube", url="https://www.youtube.com/channel/UCykfir9alToieakIrjGz8Qw")]]
    youtube_kb = InlineKeyboardMarkup(inline_keyboard=youtube_link)
    photo_about = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\pic\about_1.jpg',
                             filename='about_1.jpg')
    await message.answer_photo(photo=photo_about)
    await message.answer(td.about_company, reply_markup=youtube_kb)


@dp.message(F.text.contains("Должностные инструкции"))
async def instructions(message: Message):
    info_kb = InlineKeyboardMarkup(inline_keyboard=instructions_keybord(message), resize_keyboard=True)
    await message.answer(f"Нажми на название инструкции, чтобы открыть ссылку", reply_markup=info_kb)


@dp.message(F.text.contains("Правила внутреннего трудового распорядка"))
async def corporat_rools(message: Message):
    kb_link = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Правила ВТР", url="https://google.com"),
            InlineKeyboardButton(text="Правила ВТР", url="https://yandex.ru"),
            InlineKeyboardButton(text="Правила ВТР", url="https://jetbrains.com")
        ]
    ])
    await message.answer("Ссылки", reply_markup=kb_link)


@dp.message(F.text.contains("Схема работы служебного транспорта"))
async def navigation(message: Message):
    await message.answer(f"Вот схема служебного транспорта:")
    dep_point = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\pic\dep_point.jpg',
                             filename='dep_point.jpg')
    await message.answer_photo(photo=dep_point)
    await message.answer(f"{td.transport}")


@dp.message(F.text.contains("Правила пользования кухней и душевой"))
async def vacancy_list(message: Message):
    await message.answer(f"{td.kitchen}")


@dp.message(F.text.contains("Видео о компании"))
async def video(message: Message):
    video_kb = InlineKeyboardMarkup(inline_keyboard=video_keybord())
    await message.answer(f"Вот видео о компании:", reply_markup=video_kb)


@dp.message(Command("help"))
async def help(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="О боте", callback_data="о боте"),
            InlineKeyboardButton(text="Как пользоваться ботом", callback_data="как пользоваться ботом"),
        ],[
            InlineKeyboardButton(text="Как связаться с сотрудниками HR отдела", callback_data="контакты hr"),
        ]
    ])
    await message.answer("Доступные разделы:", reply_markup=kb)


@dp.callback_query(F.data == "о боте")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"О боте:")
    await callback.message.answer(f"{td.about_bot}")


@dp.callback_query(F.data == "как пользоваться ботом")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Как пользоваться ботом:")
    await callback.message.answer(f"{td.how_to_use}")


@dp.callback_query(F.data == "контакты hr")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Как связаться с сотрудниками HR отдела:")
    await callback.message.answer(f"{td.contacts}")


@dp.callback_query(F.data == "about_company")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Приветственное видео:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\welcom.mp4',
                             filename='welcom.mp4')
    await callback.message.answer_video(video=video_file)


@dp.callback_query(F.data == "our_product_1")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция1:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(1).mp4',
                             filename='product(1).mp4')
    await callback.message.answer_video(video=video_file)


@dp.callback_query(F.data == "our_product_2")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция2:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(2).mp4',
                             filename='product(2).mp4')
    await callback.message.answer_video(video=video_file)


@dp.callback_query(F.data == "our_product_3")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция3:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(3).mp4',
                             filename='product(3).mp4')
    await callback.message.answer_video(video=video_file)


@dp.callback_query(F.data == "our_product_4")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция4:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(4).mp4',
                             filename='product(4).mp4')
    await callback.message.answer_video(video=video_file)


@dp.message(Command("tokens"))
async def tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        await message.answer(f"Осталось токенов: {users_df.loc[user.id,'token_capacity'] - users_df.loc[user.id, 'token_usage']}\n")
    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников. Введи ниже код должности, переданный сотрудником HR департамента:\n")


@dp.message(Command("get_tokens"))
async def get_tokens(message: Message):
    """ Функция для обновления токенов для общения с ChatGPT. При частых попытках обновления токенов пользователем, уведомляет об этом в логах"""
    user = message.from_user
    global users_df
    if user.id not in users_df.index:
        return await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников. Введи ниже код должности, переданный сотрудником HR департамента:\n")

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
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников. Введи ниже код должности, переданный сотрудником HR департамента:\n")


@dp.message()
async def handle_messages(message: Message):
    global users_df
    global post_dict
    user = message.from_user
    if message.text in post_dict.keys():
        post = post_dict.get(message.text)
        await message.answer(f"Ваша должность по штатному расписанию - {post}\n")
        users_df.loc[user.id] = [4000, 0, message.date, 4000, 0, 0, '[]', message.chat.id, message.text, post_dict.get(message.text), False]
        logger.info(f"Зарегистрировался новый пользователь: {user.id}, добавлена запись в users_df")
        return await message.answer(f"Я запомнил тебя, {user.full_name}, можешь вернуться к основному меню нажав /start\n")

    if user.id in users_df.index:

        if users_df.loc[user.id, 'token_usage'] >= users_df.loc[user.id, 'token_capacity']:
            logger.info("У пользователя закончились токены")
            return await message.answer('Закончились токены, попробуй написать позже')

        context = loads(users_df.loc[user.id, 'context'])
        context.append({"role": 'user', "content": message.text})

        context_len = users_df.loc[user.id, 'context_length']

        while context_len > users_df.loc[user.id, 'context_capacity']:
            context_len -= len(context[0]['content'])
            context = context[1:]

        await message.answer('Дай подумаю...')
        # Процесс поиска вынесен в отдельный файл search.py
        search_res = proccess_search_openai(GOOGLE_API_KEY,
                                            SEARCH_ENGINE_ID,
                                            message.text)
        context.append({"role": 'system', "content": f'Вот информация из интернета: {search_res}'})
        gpt_answer = get_gpt_response(context)

        if gpt_answer['msg'] == 'Failed':
            logger.info("Что то пошло не так с запросом к OpenAI в функции get_gpt_response")
            return await message.answer('Что-то пошло не так...')

        response = gpt_answer['response']
        await message.answer(response.choices[0].message["content"])

        context.append({"role": 'user', "content": response.choices[0].message["content"]})
        token_usage = response['usage']['total_tokens']

        users_df.loc[user.id, 'context'] = dumps(context)
        users_df.loc[user.id, 'token_usage'] += token_usage
        users_df.loc[user.id, 'context_length'] += len(response.choices[0].message["content"] + message.text)

    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников.\n")
        await message.answer(f"Введи ниже код должности, переданный сотрудником HR департамента:\n")


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)
    try:
        for chat in users_df['chat_id']:
            await bot.send_message(chat_id=chat, text="Бот снова работает, Вы можете вернуться к диалогу")
    except Exception as e:
        logger.debug(f"Не удалось отправить сообщения. {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")
    finally:
        users_df.to_csv('users.csv')
        logger.info("выполнено сохранение файла users.csv")
