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

from google_api import update_book_gs


# Команда старт
@admin_router.message(lambda msg: msg.content_type == ContentType.PHOTO.value)
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

    key, user_id_str, entry_id_str = qr_content.split(':')

    if key == Key.QR_BOOK.value:
        ticket_id = int(entry_id_str)

        book = await Book.get_booking_with_venue(ticket_id)

        if not book:
            await msg.answer("❌ Бронь не найдена")
            return

        if book.status != BookStatus.CONFIRMED.value:
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

        await Book.update(book_id=book.id, status=BookStatus.VISITED.value)

        await update_book_gs(
            spreadsheet_id=book.venue.gs_id,
            sheet_name=book.date_str(),
            status=BookStatus.VISITED.value,
            row=book.gs_row
        )

        # запись в журнал
        await AdminLog.add(
            admin_id=msg.from_user.id, action=AdminAction.BOOK.value, user_id=book.user_id, comment=book_text
        )

    if key == Key.QR_TICKET.value:
        ticket_id = int(entry_id_str)

        ticket = await Ticket.get_full_ticket(ticket_id)

        if not ticket:
            await msg.answer("❌ Билет не найдена")
            return

        if ticket.status != BookStatus.CONFIRMED.value:
            await msg.answer("❌ Уже была использована")
            return

        if not ticket.is_active:
            await msg.answer("❌ Билет не активен")
            return

        ticket_text = ut.get_ticket_text(ticket)
        await msg.answer(f"✅ Билет подтверждена\n\n{ticket_text}")

        await bot.send_message(
            chat_id=ticket.user_id, text=f'✅ Ваш билет подтвержден\n\n{ticket_text}\nДобро пожаловать!'
        )

        await Ticket.update(ticket_id=ticket.id, status=BookStatus.VISITED.value)

        await update_book_gs(
            spreadsheet_id=ticket.event.venue.event_gs_id,
            sheet_name=ticket.event.gs_page,
            status=BookStatus.VISITED.value,
            row=ticket.gs_row
        )

        # запись в журнал
        await AdminLog.add(
            admin_id=msg.from_user.id, action=AdminAction.TICKET.value, user_id=ticket.user_id, comment=ticket_text
        )





