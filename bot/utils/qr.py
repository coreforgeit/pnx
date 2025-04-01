import segno
import os
import random
from aiogram.types import FSInputFile, BufferedInputFile

from PIL import Image
from io import BytesIO

from init import bot
from settings import conf


async def generate_and_sand_qr(chat_id: int, qr_data: str, caption: str = None) -> str:
    qr = segno.make_qr(qr_data, error="H")

    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=12, dark='green')
    buffer.seek(0)

    photo = BufferedInputFile(file=buffer.read(), filename=f'{qr_data}.png')
    sent = await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    return sent.photo[0].file_id

