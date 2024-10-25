from main import *
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.state import State, StatesGroup


@edit_message_router.edited_message()
async def message_editing(message: Message):
    await message.answer(f"Сообщение отредактировано")


class Interwiew(StatesGroup):
    name = State()
    age = State()
    phone = State()
    resume = State()


@interview_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(Interwiew.name)
    await message.answer(f"Привет, как тебя зовут?")


@interview_router.message(Interwiew.name)
async def name_process(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Interwiew.age)

    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=
    [
        [
            KeyboardButton(text="10-20"),
            KeyboardButton(text="21-30"),
            KeyboardButton(text="31-40"),
            KeyboardButton(text="41-50"),
            KeyboardButton(text="51-60"),
            KeyboardButton(text="61-70"),
            KeyboardButton(text="71-80"),
            KeyboardButton(text="81-300"),
        ]
    ], one_time_keyboard=True)
    await message.answer(f"Сколько тебе лет?", reply_markup=reply_keyboard)


@interview_router.message(Interwiew.age)
async def age_process(message: Message, state: FSMContext):
    await message.answer(f"Теперь укажи свой телефон", reply_markup=ReplyKeyboardRemove())
    await state.update_data(age=message.text)
    await state.set_state(Interwiew.phone)


@interview_router.message(Interwiew.phone)
async def phone_process(message:Message, state: FSMContext):
    data = await state.update_data(phone=message.text)
    await message.answer(f"Вот что я теперь о тебе знаю:")
    await summary(message,data)
    await state.clear()


async def summary(message: Message, data: dict):

    for key, value in data.items():
        await message.answer(f"{key}: {value}")

