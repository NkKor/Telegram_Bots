import asyncio
import logging
import sys
import os
import dotenv
import prep.database as database

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

import prep.models as models
from sqlalchemy.exc import NoResultFound

dotenv.load_dotenv()

token = os.getenv('TOKEN')

dp = Dispatcher()

database.add_tables()


@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user

    session = database.SessionLocal()
    new_user = models.User(user_id=user.id)
    try:
        db_user = session.query(models.User).filter(models.User.user_id == user.id).one()
        token_limit = db_user.token_limit
        token_usage = db_user.token_usage
    except NoResultFound:
        try:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            token_usage = new_user.token_usage
            token_limit = new_user.token_limit
        except Exception:
            raise Exception

    await message.answer(f'Hi, {message.from_user.first_name}.\n\n'
                         f'Your current token quota is: {token_limit - token_usage}.')


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user

    session = database.SessionLocal()

    try:
        db_user = session.query(models.User).filter(models.User.user_id == user.id).one()
        user_messages = session.query(models.Messages).filter(models.Messages.user_id == user.id)
        new_message = models.Messages(user_id=user.id,
                                      user_message=message.text)
        session.add(new_message)
        session.commit()
        session.refresh(new_message)
        for element in user_messages:
            await message.answer(element.user_message)

    except NoResultFound:
        await message.answer('Сначала зарегистрируйтесь!')


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    asyncio.run(main())
