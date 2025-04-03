from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.enums.content_type import ContentType
from io import BytesIO
from datetime import datetime

import os

import keyboards as kb
import utils as ut
from db import User, Book
from settings import conf, log_error
from init import dp, bot
from data import texts_dict
from enums import UserCB, UserStatus, Key

from google_api import update_book_gs


# Команда старт
@dp.message(lambda msg: msg.content_type == ContentType.PHOTO.value)
async def qr_check(msg: Message, state: FSMContext):
    user = await User.get_by_id(msg.from_user.id)
    if user.status == UserStatus.USER.value and not conf.debug:
        await msg.answer('❌ Доступно только администраторам')
        return

    await msg.delete()
    file_bytes = await msg.bot.download(file=msg.photo[-1].file_id, destination=BytesIO())

    file_bytes.seek(0)
    data = file_bytes.read()

    qr_content = ut.decode_qr_from_bytes(data)

    if not qr_content:
        await msg.answer("Не удалось распознать QR-код 😞")
        return

    key, user_id_str, book_id_str = qr_content.split(':')

    if key == Key.QR_BOOK.value:
        book_id = int(book_id_str)

        book = await Book.get_booking_with_venue(book_id)

        if not book:
            await msg.answer("❌ Бронь не найдена")
            return

        if book.is_come:
            await msg.answer("❌ Уже была использована")
            return

        if not book.is_active:
            await msg.answer("❌ Уже была отменена")
            return

        book_text = ut.get_book_text(book)
        await msg.answer(f"✅ Бронь подтверждена\n\n{book_text}")

        await bot.send_message(
            chat_id=book.user_id, text=f'✅ Ваша бронь подтверждена\n\n{book_text}\n\nДобро пожаловать!'
        )

        await Book.update(book_id=book.id, is_come=True)

        await update_book_gs(
            spreadsheet_id=book.venue.gs_id,
            sheet_name=book.date_book_str(),
            attended=True,
            row=book.gs_row
        )




