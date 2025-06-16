from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.enums.content_type import ContentType
from io import BytesIO
from datetime import datetime

import os

import keyboards as kb
import utils as ut
from db import User, Book, AdminLog, Ticket
from settings import conf, log_error
from init import bot, admin_router
from data import texts_dict
from enums import UserCB, UserStatus, Key, BookStatus, AdminAction

from google_api import update_book_status_gs


# Команда старт
@admin_router.message(lambda msg: msg.content_type == ContentType.PHOTO.value)
async def qr_check(msg: Message, state: FSMContext):
    user = await User.get_by_id(msg.from_user.id)
    if user.status == UserStatus.USER.value and not conf.debug:
        await msg.answer('❌ Доступно только администраторам')
        return

    await msg.delete()

    file_bytes = await msg.bot.download(file=msg.photo[-1].file_id, destination=BytesIO())
    # file_bytes = await bot.download(file=file_id, destination=BytesIO())

    file_bytes.seek(0)
    data = file_bytes.read()

    qr_content = ut.decode_qr_from_bytes(data)

    if not qr_content:
        await msg.answer("Не удалось распознать QR-код 😞")
        # await bot.send_message(user_id, "Не удалось распознать QR-код 😞")
        return

    if qr_content.startswith(conf.bot_link):
        _, key, user_id_str, entry_id_str = qr_content[len(conf.bot_link):].split('-')
    else:
        key, user_id_str, entry_id_str = qr_content.split(':')

    await ut.qr_checking(user_id=msg.from_user.id, key=key, entry_id_str=entry_id_str)

