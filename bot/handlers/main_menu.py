from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, Any
from aiogram.filters.command import CommandStart, Command
from aiogram.filters.state import StateFilter
from aiogram.filters import BaseFilter
from aiogram import Router

import json

import keyboards as kb
import utils as ut
from db import User, Book, Ticket
from settings import conf, log_error
from init import main_router, bot, redis_client
from data import texts_dict
from handlers.user.user_utils import send_start_ticket_msg, send_main_settings_msg
from enums import UserCB, MenuCommand, Key


# Команда старт
@main_router.message(CommandStart())
async def com_start(msg: Message, state: FSMContext):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)

    access_id = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else None
    print(msg.text)
    print(access_id)

    if access_id:
        key = f"{Key.ADD_ADMIN.value}{access_id}"
        admin_data = ut.get_redis_data(key)

        if not admin_data:
            await msg.answer('⚠️ Ссылка устарела или уже была использована')

        else:
            print(type(admin_data))
            await User.update(
                user_id=msg.from_user.id,
                status=admin_data['user_status'],
                venue_id=admin_data['venue_id'],
            )
            await msg.answer('✅ Статус обновлён')

    await ut.get_start_msg(user=msg.from_user)


# проверяет подписку, в случае удачи пропускает
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.BACK_START.value))
async def back_com_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await ut.get_start_msg(user=cb.from_user, msg_id=cb.message.message_id)


# Команда начать бронировать
@main_router.message(Command(MenuCommand.BOOK.command))
async def com_book(msg: Message, state: FSMContext):
    await state.clear()

    await ut.get_start_book_msg(user=msg.from_user)


# Команда старт
@main_router.message(Command(MenuCommand.TICKET.command))
async def com_ticket(msg: Message, state: FSMContext):
    await state.clear()

    await send_start_ticket_msg(chat_id=msg.from_user.id)


# Команда мои брони
@main_router.message(Command(MenuCommand.SETTINGS.command))
async def com_settings(msg: Message, state: FSMContext):
    await state.clear()

    await send_main_settings_msg(msg.from_user.id)


# показывает кр
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.VIEW_QR.value))
async def book_comment(cb: CallbackQuery, state: FSMContext):
    _, type_qr, entry_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)

    if type_qr == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)
        await cb.message.answer_photo(photo=book.qr_id, caption=ut.get_book_text(book))

    elif type_qr == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)
        await cb.message.answer_photo(photo=ticket.qr_id, caption=ut.get_ticket_text(ticket))


# удаляет сообщение
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.VIEW_QR.value))
async def book_comment(cb: CallbackQuery, state: FSMContext):
    _, type_qr, entry_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)

    if type_qr == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)
        await cb.message.answer_photo(photo=book.qr_id, caption=ut.get_book_text(book))

    elif type_qr == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)
        await cb.message.answer_photo(photo=ticket.qr_id, caption=ut.get_ticket_text(ticket))

