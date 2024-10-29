import asyncio
import logging
import sys
import os
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from openai import OpenAI


load_dotenv()
client = OpenAI()
token = os.getenv('TOKEN')
logger = logging.getLogger(__name__)
dp = Dispatcher()


gpt_model = 'gpt-4o-mini-2024-07-18'
gpt_prefix = "представь что ты поэт, отвечай используя исходный текст запроса, но возвращай его в построчно рифмованной форме"
gpt_sufix = "проверь, чтобы твой ответ использовал исходный текст запроса с добавлением необходимых для рифмы слов"


def get_gpt_response(context, model=gpt_model, max_tokens=1000, temperature=0.7, n=1):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": gpt_prefix},
            {"role": "user", "content": context},
            {"role": "system", "content": gpt_sufix},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        n=1
    )
    return response


@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    await message.answer(f"Приветствую тебя, {user.full_name}, что будем рифмовать сегодня?")


@dp.message()
async def handle_messages(message: Message):
    user = message.from_user
    riphme = ""
    try:
        response = get_gpt_response(message.text)
        riphme = response.choices[0].message['content']
    except Exception as e:
        logger.info(f"{user.full_name} ошибка при обработке запроса в openai: {e}")
    await message.reply(f"\n{riphme}")


async def main():
    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Работа бота остановлена")