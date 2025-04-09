from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from dataclasses import asdict
from datetime import datetime

import asyncio

import db
import keyboards as kb
import utils as ut
from google_api import add_book_gs
from db import User, Book, Event, Ticket
from settings import conf, log_error
from init import user_router, bot
from data import texts_dict
from enums import UserCB, BookData, TicketData, TicketStep, book_text_dict, ticket_text_dict, Key


async def send_main_book_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.print_all()

    people_count = data_obj.people_count
    if data_obj.people_count and data_obj.people_count >= 5:
        people_count = 'компания'

    row_list = [
        f'<b>{data_obj.venue_name}</b>\n\n',
        f'Дата: {data_obj.date_str}\n',
        f'Время: {data_obj.time_str}\n',
        f'Количество персон: {people_count}\n',
        f'Комментарий: {data_obj.comment}\n',
    ]
    text = ''.join(row for row in row_list if 'None' not in row).strip()

    text += f'\n\n{book_text_dict.get(data_obj.step)}'

    await bot.edit_message_text(
        chat_id=data_obj.user_id,
        message_id=data_obj.msg_id,
        text=text,
        reply_markup=markup
    )


async def send_start_ticket_msg(chat_id: int, msg_id: int = None):
    if msg_id:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)

    events = await Event.get_all()
    if events:
        text = '<b>Предстоящие мероприятия:</b>'
    else:
        text = '<b>В ближайшее время мероприятий не запланировано</b>'

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb.get_ticket_event_kb(events))


async def send_main_ticket_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = TicketData(**data)

    data_obj.print_all()
    print(type(data_obj.event))

    # event = Event(**data_obj.event) if data_obj.event else Event()
    event = data_obj.event if data_obj.event else Event()

    row_list = [
        f"<b>{event.name}</b>\n",
        # f"Дата: {data_obj.date_str}\n",
        # f"Время: {data_obj.time_str}\n",
        f"Категория: {data_obj.option.name if data_obj.option else None}\n",
        f"Количество билетов: {data_obj.count_place}\n",
    ]

    text = ''.join(r for r in row_list if 'None' not in r and r.strip())

    text += f'\n\n📝 {ticket_text_dict.get(data_obj.step)}'

    if data_obj.msg_id:
        await bot.edit_message_text(
            chat_id=data_obj.user_id,
            message_id=data_obj.msg_id,
            text=text,
            reply_markup=markup
        )

    else:
        await bot.send_message(
            chat_id=data_obj.user_id,
            text=text,
            reply_markup=markup
        )


# Основное сообщение по настройкам
async def send_main_settings_msg(user_id: int):
    books = await Book.get_all_user_booking(user_id=user_id)
    tickets = await Ticket.get_all_user_tickets(user_id=user_id)

    all_book_count = len(books) + len(tickets)

    if all_book_count == 0:
        await bot.send_message(
            chat_id=user_id, text=f'🤷‍♂️ У вас нет активных броней', reply_markup=kb.get_back_start_kb()
        )
        return

    for book in books:
        await bot.send_message(
            chat_id=user_id,
            text=ut.get_book_text(book),
            reply_markup=kb.get_user_manage_book_kb(book_type=Key.QR_BOOK.value, entry_id=book.id)
        )

    for ticket in tickets:
        await bot.send_message(
            chat_id=user_id,
            text=ut.get_ticket_text(ticket),
            reply_markup=kb.get_user_manage_book_kb(book_type=Key.QR_TICKET.value, entry_id=ticket.id)
        )






