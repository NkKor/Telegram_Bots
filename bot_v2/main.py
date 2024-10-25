import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram import Router
from openai import OpenAI
from aiogram import Router, types


load_dotenv()
client = OpenAI()
token = os.getenv('TOKEN')

logger = logging.getLogger(__name__)
interview_router = Router()
edit_message_router = Router()


async def main():
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(interview_router)
    dp.include_router(edit_message_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")
    finally:
        pass