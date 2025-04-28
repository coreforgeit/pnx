from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from db import Ticket, Event, EventOption, Venue
from settings import conf, log_error
from init import user_router, bot
from google_api import add_ticket_row_to_registration
from enums import UserCB, BookStatus, TicketData, TicketStep, ticket_text_dict, UserState, Action, Key


async def confirm_tickets(user_id: int, full_name: str, ticket_id_list: list[int]):
    ticket_id = 0
    ticket = None
    for ticket_id in ticket_id_list:
        ticket = await Ticket.get_full_ticket(ticket_id)
        qr_data = f'{Key.QR_TICKET.value}:{user_id}:{ticket_id}'
        text = ut.get_ticket_text(ticket)
        # сохраняем кр
        qr_photo_id = await ut.generate_and_sand_qr(chat_id=user_id, qr_data=qr_data, caption=text)

        # last_row = await Ticket.get_max_event_row(ticket.event.id)

        #     записать в таблицу
        await add_ticket_row_to_registration(
            spreadsheet_id=ticket.event.venue.event_gs_id,
            page_id=ticket.event.gs_page,
            ticket_id=ticket_id,
            option_name=ticket.option.name,
            user_name=full_name,
            ticket_row=ticket.gs_row
        )

        await Ticket.update(ticket_id=ticket_id, qr_id=qr_photo_id, status=BookStatus.CONFIRMED.value, is_active=True)

        text = f'<b>Подтверждён билета на {ticket.event.name} пользователь {full_name}</b>'
        await bot.send_message(chat_id=ticket.event.venue.admin_chat_id, text=text)

    if ticket_id and ticket:
        ut.create_book_notice(
            book_id=ticket_id,
            book_date=ticket.event.date_event,
            book_time=ticket.event.time_event,
            book_type=Key.QR_TICKET.value
        )