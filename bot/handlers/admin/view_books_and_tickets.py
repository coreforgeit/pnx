from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime

import asyncio

import keyboards as kb
import utils as ut
from .admin_utils import send_start_view_msg
from db import User, Ticket, Book, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router
from enums import AdminCB, UserState, Action, Key, SendData, UserStatus, MailingData


# старт просмотра броней
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.VIEW_START.value))
async def manage_event_start(cb: CallbackQuery, state: FSMContext):
    _, book_type = cb.data.split(':')
    await state.clear()

    admin = await User.get_admin(cb.from_user.id)

    await send_start_view_msg(chat_id=cb.from_user.id, book_type=book_type, admin=admin, msg_id=cb.message.message_id)


# просмотра броней за день
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.VIEW_BOOK.value))
async def view_book(cb: CallbackQuery, state: FSMContext):
    _, book_type, value = cb.data.split(':')

    admin = await User.get_admin(cb.from_user.id)
    if (not admin or
            admin.status == UserStatus.USER.value or
            (admin.status == UserStatus.STAFF.value and not admin.venue_id)
    ):
        await cb.message.answer(f'❗️ Вам отказано в доступе. Обратитесь к администратору')
        return

    if book_type == Key.QR_BOOK.value:
        date_book = datetime.strptime(value, conf.date_format)
        books = await Book.get_books_by_date(date_book)
        for book in books:
            text = ut.get_book_text(book)
            await cb.message.answer(text=text, reply_markup=kb.get_book_manage_kb(book.id, book_type=book_type))
        return

    elif book_type == Key.QR_TICKET.value:
        event_id = int(value)
        tickets = await Ticket.get_all_tickets(event_id=event_id)
        for ticket in tickets:
            text = ut.get_ticket_text(ticket)
            await cb.message.answer(text=text, reply_markup=kb.get_book_manage_kb(ticket.id, book_type=book_type))

    else:
        text = f'<b>❗️ Ошибка</b>'
        await cb.message.edit_text(text=text, reply_markup=kb.get_back_start_kb())


