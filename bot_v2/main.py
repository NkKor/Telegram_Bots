import asyncio
import logging
import sys
import os
import pandas as pd
from stellar_bot import *
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from openai import OpenAI


load_dotenv()
client = OpenAI()
token = os.getenv('TOKEN')
logger = logging.getLogger(__name__)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')


async def main():
    global users_df
    bot = Bot(token=token)
    dp.include_router(employee_router)
    await dp.start_polling(bot)
    try:
        for chat in users_df['chat_id']:
            await bot.send_message(chat_id=chat, text="Бот снова работает, Вы можете вернуться к диалогу")
    except Exception as e:
        logger.info(f"Не удалось отправить сообщения старым пользователям. {e}")

if __name__ == '__main__':
    global users_df
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")
    finally:
        users_df.to_csv('users.csv', index=False)
        logger.info("выполнено сохранение файла users.csv")