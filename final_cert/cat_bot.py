import asyncio
import logging
import sys
import os
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from openai import OpenAI


load_dotenv()
client = OpenAI()
token = os.getenv('TOKEN')
logger = logging.getLogger(__name__)
dp = Dispatcher()


def generate_img_link(description):
    response = client.images.generate(
        model="dall-e-3",
        prompt=description,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url


@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    await message.answer(f"Приветствую тебя, {user.full_name}")


@dp.message(Command("cat"))
async def cat_image(message: Message, bot):
    user = message.from_user
    image = generate_img_link(description="Котик")
    photo = FSInputFile(image)
    await bot.send_photo(chat_id=user.id, photo=photo)


@dp.message()
async def handle_messages(message: Message):
    await message.reply(f"\n{message.text}")


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