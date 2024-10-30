import json
from datetime import timedelta
from aiogram import Bot, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from json import loads, dumps
from search import proccess_search_openai
from prompt_parser import Parser
import dalle_img_gen as dalle
from main import *
from gpt_ai import get_gpt_response
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import tdata as td
import pandas as pd


dp = Dispatcher()
employee_router = Router()
hr_manager_router = Router()
post_dict = td.posts
post_learn_links = td.post_learn_links
logger = logging.getLogger(__name__)

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
            'is_new',
            'is_hr_manager',
            'is_fired'
        ]
    )
    users_df.to_csv('users.csv', index=False)
users_df = pd.read_csv("users.csv", index_col='user_id')


def new_employee_keyboard():
    keybord = [[
            KeyboardButton(text='Пройти входное интервью (demo)'),
        ],[
            KeyboardButton(text='Видео о компании'),
            KeyboardButton(text='Информация о компании'),
        ],[
            KeyboardButton(text='Правила трудового распорядка'),
            KeyboardButton(text='Должностные инструкции'),
        ],[
            KeyboardButton(text='Схема работы служебного транспорта'),
        ],[
            KeyboardButton(text='Правила пользования кухней и душевой'),
        ],
    ]
    return keybord


def employee_keyboard():
    keybord = [
        [
            KeyboardButton(text='Информация о компании'),
            KeyboardButton(text='Должностные инструкции'),
        ],[
            KeyboardButton(text='Правила трудового распорядка'),
        ],[
            KeyboardButton(text='Пройти опрос об удовлетворенности (demo)'),
        ],[
            KeyboardButton(text='Тест по инструкциям(demo)'),
            KeyboardButton(text='Сообщить о проблеме(demo)'),
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
        logger.debug("Провал с запросом списка инструкций!!!")

    link_list = post_learn_links.get(current_user_post)
    keyboard = []
    try:
        for n, link in enumerate(link_list):
            keyboard.append([InlineKeyboardButton(text=f'Инструкция # {n}', url=link)])
    except Exception as e:
        logger.debug("Провал с формированием списка должностных инструкций!!!")
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


class Employee(StatesGroup):
    main = State()
    certification = State()
    training = State()
    fired = State()


class NewEmployee(StatesGroup):
    first_enter = State()
    main = State()
    welcome_interview = State()
    transfer_to_employee = State()


@employee_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    global users_df
    user = message.from_user
    new_kb = ReplyKeyboardMarkup(keyboard=new_employee_keyboard(), resize_keyboard=True, one_time_keyboard=True)
    main_kb = ReplyKeyboardMarkup(keyboard=employee_keyboard(), resize_keyboard=True, one_time_keyboard=True)
    if user.id in users_df.index:
        if users_df.loc[user.id, 'is_new']:
            await message.answer(f"Выбери то, что тебя интересует в меню ниже", reply_markup=new_kb)
        else:
            await message.answer(f"Выбери то, что тебя интересует в меню ниже", reply_markup=main_kb)
        await message.answer(f"Нажми /help, если нужна помощь")

    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников.\n")
        await message.answer(f"Введи ниже код должности, переданный сотрудником HR департамента:\n")
        await state.set_state(NewEmployee.first_enter)


@employee_router.message(F.text.contains("Draw"))
async def gen_img(message: types.Message, bot):
    """Обработчик запроса на создание рисунка с помощью DALL-E API
    Реализация обработки запроса в API представлена в файле dalle_img_gen.py"""
    user = message.from_user
    user_img_description = message.text

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {"role": "system", "content": f"Check safety and ethical aspect of user message, remove harmful deatils if there are"},
            {"role": "user", "content": user_img_description},
        ],
    )
    img_description = response.choices[0].message.content
    await message.answer("Подожди, выполняется генерация...")
    instruction_prompt = [
        {"role": "system", "content": f"Reply as a helpful AI assistant"},
        {"role": "user", "content": img_description},
        {'role': 'system', 'content': 'Answer in json format: '
                                      '{"text": your text response,'
                                      ' "picture": prompt for image generation}'},
        {"role": "user", "content": 'Double check your answer is correct json.'},
    ]
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=instruction_prompt,
    )
    text_response = response.choices[0].message.content
    try:
        response_data = json.loads(text_response)
        try:
            await message.answer(response_data['text'])
            images = dalle.d3_image_generate(description=response_data['picture'], user_id=user.id)
            for image in images:
                photo = FSInputFile(image)
                await bot.send_photo(chat_id=user.id, photo=photo)
        except Exception as e:
            logger.info(f"Генерация изображения из команды 'Draw and tell' провалена{e}")

    except Exception as e:
        logger.debug(f"Не удалось распарсить ответ от openai{e}")
        return await message.answer(text_response)
    finally:
        pass


"""@dp.message(Command("variate"))
async def variate_img(message: types.Message, bot):
    #Обработчик запроса на создание вариации рисунка с помощью DALL-E API
    #Реализация обработки запроса в API представлена в файле dalle_img_gen.py
    user = message.from_user
    msg_photo = bot.get_file(message.photo[-1].file_id)
    with open('image.png', 'wb') as photo_file:
        photo_file.write(msg_photo)
    await message.answer("Подожди, выполняется генерация...")
    try:
        image = dalle.generate_image_variation(msg_photo, user.id)
        photo = FSInputFile(image)
        return bot.send_photo(chat_id=user.id, photo=photo)
    except Exception as e:
        logger.debug(f"Генерация изображения провалена{e}")"""


@employee_router.message(F.text.contains("Информация о компании"))
async def video(message: Message):
    youtube_link = [[InlineKeyboardButton(text="Видео о компании на Youtube", url="https://www.youtube.com/channel/UCykfir9alToieakIrjGz8Qw")]]
    youtube_kb = InlineKeyboardMarkup(inline_keyboard=youtube_link)
    photo_about = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\pic\about_1.jpg',
                             filename='about_1.jpg')
    await message.answer_photo(photo=photo_about)
    await message.answer(td.about_company, reply_markup=youtube_kb)


@employee_router.message(F.text.contains("Должностные инструкции"))
async def instructions(message: Message):
    info_kb = InlineKeyboardMarkup(inline_keyboard=instructions_keybord(message), resize_keyboard=True)
    await message.answer(f"Нажми на название инструкции, чтобы открыть ссылку", reply_markup=info_kb)


@employee_router.message(F.text.contains("Правила внутреннего трудового распорядка"))
async def corporat_rools(message: Message):
    kb_link = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Правила ВТР", url="https://google.com"),
            InlineKeyboardButton(text="Правила ВТР", url="https://yandex.ru"),
            InlineKeyboardButton(text="Правила ВТР", url="https://jetbrains.com")
        ]
    ])
    await message.answer("Ссылки", reply_markup=kb_link)


@employee_router.message(F.text.contains("Схема работы служебного транспорта"))
async def navigation(message: Message):
    await message.answer(f"Вот схема служебного транспорта:")
    dep_point = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\pic\dep_point.jpg',
                             filename='dep_point.jpg')
    await message.answer_photo(photo=dep_point)
    await message.answer(f"{td.transport}")


@employee_router.message(F.text.contains("Правила пользования кухней и душевой"))
async def vacancy_list(message: Message):
    await message.answer(f"{td.kitchen}")


@employee_router.message(F.text.contains("Видео о компании"))
async def video(message: Message):
    video_kb = InlineKeyboardMarkup(inline_keyboard=video_keybord())
    await message.answer(f"Вот видео о компании:", reply_markup=video_kb)


@employee_router.message(Command("help"))
async def help(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="О боте", callback_data="о боте"),
            InlineKeyboardButton(text="Как пользоваться ботом", callback_data="как пользоваться ботом"),
        ],[
            InlineKeyboardButton(text="Как связаться с сотрудниками HR отдела", callback_data="контакты hr"),
        ]
    ])
    await message.answer("Чтобы вернуться к основному меню, нажмите /start")
    await message.answer("Доступные разделы помощи:", reply_markup=kb)


@employee_router.callback_query(F.data == "о боте")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"О боте:")
    await callback.message.answer(f"{td.about_bot}")


@employee_router.callback_query(F.data == "как пользоваться ботом")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Как пользоваться ботом:")
    await callback.message.answer(f"{td.how_to_use}")


@employee_router.callback_query(F.data == "контакты hr")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Как связаться с сотрудниками HR отдела:")
    await callback.message.answer(f"{td.contacts}")


@employee_router.callback_query(F.data == "about_company")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Приветственное видео:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\welcom.mp4',
                             filename='welcom.mp4')
    await callback.message.answer_video(video=video_file)


@employee_router.callback_query(F.data == "our_product_1")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция1:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(1).mp4',
                             filename='product(1).mp4')
    await callback.message.answer_video(video=video_file)


@employee_router.callback_query(F.data == "our_product_2")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция2:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(2).mp4',
                             filename='product(2).mp4')
    await callback.message.answer_video(video=video_file)


@employee_router.callback_query(F.data == "our_product_3")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция3:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(3).mp4',
                             filename='product(3).mp4')
    await callback.message.answer_video(video=video_file)


@employee_router.callback_query(F.data == "our_product_4")
async def answer(callback: CallbackQuery):
    await callback.message.edit_text(f"Наша продукция4:")
    video_file = FSInputFile(path=r'C:\Users\Z0rg3\PycharmProjects\Telegram_Bots\hr_bot\video\product(4).mp4',
                             filename='product(4).mp4')
    await callback.message.answer_video(video=video_file)


@employee_router.message(Command("tokens"))
async def tokens(message: Message):
    user = message.from_user
    global users_df
    if user.id in users_df.index:
        await message.answer(f"Осталось токенов: {users_df.loc[user.id,'token_capacity'] - users_df.loc[user.id, 'token_usage']}\n")
    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников. Введи ниже код должности, переданный сотрудником HR департамента:\n")


@employee_router.message(Command("get_tokens"))
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


@employee_router.message(Command("clear"))
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


@employee_router.message(NewEmployee.first_enter)
async def new_employee_reg(message: Message, state: FSMContext):
    global users_df
    global post_dict
    user = message.from_user
    new_kb = ReplyKeyboardMarkup(keyboard=new_employee_keyboard(), resize_keyboard=True, one_time_keyboard=True)
    if message.text in post_dict.keys():
        post = post_dict.get(message.text)
        await message.answer(f"Ваша должность по штатному расписанию - {post}\n")
        users_df.loc[user.id] = [4000, 0, message.date, 4000, 0, 0, '[]',
                                     message.chat.id, message.text, post_dict.get(message.text),
                                     True, False, False]
        logger.info(f"Зарегистрировался новый пользователь: {user.id}, добавлена запись в users_df")
        users_df.to_csv('users.csv')
        await message.answer(f"Добро пожаловать в компанию {message.from_user.full_name}!"
                                 f"Теперь Вам доступно меню сотрудника.")
    else:
        return message.answer(f"Такой должности нет в базе. Свяжитесь с руководителем или убедитесь, что вы правильно ввели код должности.")
    await state.clear()
    await message.answer(f"Выберите интересующий Вас раздел.", reply_markup=new_kb)
    await message.answer(f"Нажми /help, если нужна помощь")


@employee_router.message()
async def handle_messages(message: Message, state: FSMContext):
    user = message.from_user
    new_kb = ReplyKeyboardMarkup(keyboard=new_employee_keyboard(), resize_keyboard=True, one_time_keyboard=True)
    main_kb = ReplyKeyboardMarkup(keyboard=employee_keyboard(), resize_keyboard=True, one_time_keyboard=True)
    if user.id not in users_df.index:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников.\n")
        await message.answer(f"Введи ниже код должности, переданный сотрудником HR департамента:\n")
        return state.set_state(NewEmployee.first_enter)
    else:
        if users_df.loc[user.id, 'is_new']:
            await message.answer(f"Выбери то, что тебя интересует в меню ниже", reply_markup=new_kb)
        else:
            await message.answer(f"Выбери то, что тебя интересует в меню ниже", reply_markup=main_kb)
        await message.answer(f"Нажми /help, если нужна помощь")

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
        """search_res = proccess_search_openai(GOOGLE_API_KEY,
                                            SEARCH_ENGINE_ID,
                                            message.text)
        context.append({"role": 'system', "content": f'Вот информация из интернета: {search_res}'})"""

        try:
            gpt_answer = get_gpt_response(context)
        except Exception as e:
            logger.debug("Что то пошло не так с запросом к OpenAI в функции get_gpt_response")
            return await message.answer('Что-то пошло не так c ChatGpt, попробуте позже...')

        response = gpt_answer
        await message.answer(response.choices[0].message.content)
        context = Parser(context)._parse_prompt()
        await message.answer(Parser(context).get_parsed_text())

        context.append({"role": 'user', "content": response.choices[0].message.content})
        token_usage = response['usage']['total_tokens']

        users_df.loc[user.id, 'context'] = dumps(context)
        users_df.loc[user.id, 'token_usage'] += token_usage
        users_df.loc[user.id, 'context_length'] += len(response.choices[0].message.content + message.text)

    else:
        await message.answer(f"Приветствую тебя, {user.full_name}, тебя нет в базе сотрудников.\n")
        await message.answer(f"Введи ниже код должности, переданный сотрудником HR департамента:\n")
        return state.set_state(NewEmployee.first_enter)

