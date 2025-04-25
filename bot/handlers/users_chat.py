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
from db import User, Ticket, Book, AdminLog, Event, Venue
from settings import conf, log_error
from init import bot, main_router
from enums import AdminCB, UserState, Action, Key, SendData, UserStatus, AdminAction


# начало переписки
@main_router.callback_query(lambda cb: cb.data.startswith(AdminCB.SEND_MESSAGE_START.value))
async def send_message_start(cb: CallbackQuery, state: FSMContext):
    _, book_type, entry_id_str, user_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)
    user_id = int(user_id_str)

    if book_type == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)
        user = await User.get_by_id(book.user_id)
        text_book = f'{ut.get_book_text(book)}'
        pre_text = f'🪑 Бронь:\n'

    elif book_type == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(ticket_id=entry_id)
        user = await User.get_by_id(ticket.user_id)
        text_book = f'{ut.get_ticket_text(ticket)}'
        pre_text = f'🎫 Билет:\n'

    else:
        text = f'<b>❗️ Ошибка</b>'
        await cb.message.edit_text(text=text, reply_markup=kb.get_back_start_kb())
        return

    sender_info = await User.get_by_id(cb.from_user.id)
    await state.set_state(UserState.SEND_MSG.value)
    data_obj = SendData(
        from_user_id=cb.from_user.id,
        book_text=text_book,
        sender_status=sender_info.status,
        book_type=book_type,
        entry_id=entry_id,
        base_msg_id=cb.message.message_id,
    )

    if sender_info.status == UserStatus.USER.value:
        data_obj.for_user_id = user_id
        text = (
            f'<u><b>ℹ️ Следующее сообщение будет отправлено администратору</b></u>\n'
            f'{pre_text}{text_book}'
        )

    else:
        data_obj.for_user_id = user.id
        text = (
            f'<u><b>ℹ️ Следующее сообщение будет отправлено пользователю {user.full_name}</b></u>\n'
            f'{pre_text}{text_book}'
        )

    await state.update_data(data=asdict(data_obj))
    await cb.message.answer(text, reply_markup=kb.get_cancel_kb())


# отправка сообщения пользователю
@main_router.message(StateFilter(UserState.SEND_MSG.value))
# @main_router.message(
#     lambda msg: msg.chat.type == ChatType.GROUP.value and msg.text and msg.text.isdigit() and len(msg.text) == 5
# )
async def mailing_preview(msg: Message, state: FSMContext):
    data = await state.get_data()
    data_obj = SendData(**data)
    data_obj.print_all()
    await state.clear()

    text = (
        f'📩 Новое сообщение по брони:\n'
        f'{data_obj.book_text}\n\n'
    )

    await bot.send_message(chat_id=data_obj.for_user_id, text=text)
    await bot.copy_message(
        chat_id=data_obj.for_user_id,
        from_chat_id=msg.chat.id,
        message_id=msg.message_id,
        parse_mode=None,
        reply_markup=kb.get_send_answer_kb(
            user_id=data_obj.from_user_id,
            book_id=data_obj.entry_id,
            book_type=data_obj.book_type
        )
    )
    # await bot.edit_message_reply_markup(
    #     chat_id=msg.from_user.id,
    #     message_id=data_obj.base_msg_id,
    #     reply_markup=kb.get_send_answer_kb(
    #         user_id=data_obj.for_user_id,
    #         book_id=data_obj.entry_id,
    #         book_type=data_obj.book_type
    #     )
    # )

    # запись в журнал
    text = msg.text or msg.caption
    if not text:
        text = msg.content_type
    if data_obj.sender_status == UserStatus.USER.value:
        await AdminLog.add(
            admin_id=data_obj.for_user_id,
            user_id=msg.from_user.id,
            action=AdminAction.USER_SEND.value,
            comment=text
        )
    else:
        await AdminLog.add(
            admin_id=msg.from_user.id,
            user_id=data_obj.for_user_id,
            action=AdminAction.ADMIN_SEND.value,
            comment=text
        )

