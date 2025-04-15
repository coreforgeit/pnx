from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from .user_utils import send_main_settings_msg, send_main_book_msg
from db import User, Book, Ticket
from settings import conf, log_error
from init import user_router, bot
from data import texts_dict
from google_api import mark_booking_cancelled
from enums import UserCB, Key, Action, UserState, BookData, BookStep, BookStatus


# проверяет подписку, в случае удачи пропускает
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.SETTINGS_START.value))
async def settings_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await send_main_settings_msg(cb.from_user.id)


# проверяет подписку, в случае удачи пропускает
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.SETTINGS_REMOVE_1.value))
async def settings_remove(cb: CallbackQuery, state: FSMContext):
    _, type_qr, entry_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)

    if type_qr == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)
        book_text = ut.get_book_text(book)
        text = (
            f'<b>❓ Вы уверены, что хотите отменить бронь?</b>\n\n'
            f'{book_text}\n\n'
            f'ℹ️<i>После отмены бронь восстановить будет невозможно</i>'
        )
        await cb.message.answer(text=text, reply_markup=kb.get_cancel_book_kb(type_qr, entry_id))

    elif type_qr == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)
        ticket_text = ut.get_ticket_text(ticket)

        text = (
            f'<b>❓ Вы уверены, что хотите вернуть билет?</b>\n\n'
            f'{ticket_text}\n\n'
            f'ℹ️<i>После возвращения билет восстановить будет невозможно</i>'
        )
        await cb.message.answer(text=text, reply_markup=kb.get_cancel_book_kb(type_qr, entry_id))


# проверяет подписку, в случае удачи пропускает
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.SETTINGS_REMOVE_2.value))
async def settings_remove(cb: CallbackQuery, state: FSMContext):
    _, type_qr, entry_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)

    if type_qr == Action.DEL.value:
        await cb.message.delete()

    elif type_qr == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)

        await mark_booking_cancelled(
            spreadsheet_id=book.venue.book_gs_id,
            page_name=book.date_str(),
            row=book.gs_row,
            book_type=type_qr
        )
        await Book.update(book_id=entry_id, status=BookStatus.CANCELED.value)

        await cb.message.answer(text=f'✅ Бронь успешно отменена')

        #     пишем админам
        book_text = ut.get_book_text(book)
        text = (
            f'❌ Отмена брони пользователем {cb.from_user.full_name}\n\n'
            f'{book_text}'
        )
        await bot.send_message(chat_id=book.venue.admin_chat_id, text=text)

    elif type_qr == Key.QR_TICKET.value:
        """тут ещё нужно добавить возврат средств"""
        ticket = await Ticket.get_full_ticket(entry_id)

        await Ticket.update(ticket_id=entry_id, status=BookStatus.CANCELED.value)
        await mark_booking_cancelled(
            spreadsheet_id=ticket.gs_sheet,
            page_id=ticket.gs_page,
            row=ticket.gs_row,
            book_type=type_qr
        )

        #     пишем админам
        ticket_text = ut.get_ticket_text(ticket)
        text = (
            f'❌ Возврат билета пользователем {cb.from_user.full_name}\n\n'
            f'{ticket_text}'
        )
        await bot.send_message(chat_id=ticket.event.venue.admin_chat_id, text=text)


# проверяет подписку, в случае удачи пропускает
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.SETTINGS_EDIT.value))
async def settings_start(cb: CallbackQuery, state: FSMContext):
    _, book_type, book_id_str = cb.data.split(':')
    book_id = int(book_id_str)
    await state.clear()

    book = await Book.get_booking_with_venue(book_id)

    await state.set_state(UserState.BOOK.value)
    data_obj = BookData()

    data_obj.user_id = cb.from_user.id
    data_obj.msg_id = cb.message.message_id
    data_obj.step = BookStep.DATE.value

    data_obj.book_id = book.id
    data_obj.book_row = book.gs_row
    data_obj.venue_id = book.venue.id
    data_obj.venue_name = book.venue.name
    data_obj.date_str = book.date_str()
    data_obj.time_str = book.time_str()
    data_obj.people_count = book.people_count
    data_obj.comment = book.comment

    await state.update_data(data=asdict(data_obj))
    await send_main_book_msg(state, markup=kb.get_book_date_kb())

    '''
@dataclass
class BookData(BaseData):
    book_id: int = None
    venue_id: int = None
    venue_name: str = None
    date_str: str = None
    time_str: str = None
    times_list: list[str] = None
    people_count: int = None
    comment: str = None
    
user_id: 524275902
msg_id: 9504
step: check
venue_id: 1
venue_name: Понаехали
date_str: 19.04.2025
time_str: 12:00
times_list: []
people_count: 3
comment: None
    '''



