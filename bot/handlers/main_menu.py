from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, Any
from aiogram.filters.command import CommandStart, Command
from aiogram.filters.state import StateFilter
from aiogram.enums.chat_type import ChatType
from aiogram import Router

import json

import keyboards as kb
import utils as ut
from db import User, Book, Ticket, Venue
from settings import conf, log_error
from init import main_router, bot, redis_client
from data import texts_dict
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.user.user_utils import send_start_ticket_msg, send_main_settings_msg, send_selected_event_msg
from .admin.admin_utils import send_start_view_msg
from enums import UserCB, MenuCommand, Key, UserStatus


# Команда старт
@main_router.message(
    lambda msg:
    (msg.chat.type == ChatType.GROUP.value or msg.chat.type == ChatType.SUPERGROUP.value)
    and msg.text
    and msg.text.isdigit()
    and len(msg.text) == 5
)
async def group_msg(msg: Message, session: AsyncSession):
    venue = await Venue.get_by_admin_chat(session=session, chat_id=int(msg.text))
    if venue:
        await Venue.update(session=session, venue_id=venue.id, chat_id=msg.chat.id)
        text = f'✅ Чат успешно добавлен как группа для заведения {venue.name}'
        await msg.answer(text)


# Команда старт
@main_router.message(CommandStart())
async def com_start(msg: Message, state: FSMContext, session: AsyncSession):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(
        session=session,
        user_id=msg.from_user.id,
        full_name=msg.from_user.full_name,
        username=msg.from_user.username,
    )
    payloads = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else None
    if payloads:
        try:

            payloads_list = payloads.split('-')
            key = payloads_list[0]

            if key == Key.ADD_ADMIN.value:
                value = payloads_list[1]

                key = f"{Key.ADD_ADMIN.value}-{value}"
                admin_data = ut.get_redis_data(key)

                if not admin_data:
                    await msg.answer('⚠️ Ссылка устарела или уже была использована')

                else:
                    await User.update(
                        session=session,
                        user_id=msg.from_user.id,
                        status=admin_data['user_status'],
                        venue_id=admin_data['venue_id'],
                    )
                    await msg.answer('✅ Статус обновлён')

            elif key == Key.QR_TICKET.value:
                value = payloads_list[1]
                event_id = int(value)
                await send_selected_event_msg(chat_id=msg.from_user.id, event_id=event_id, session=session)
                return

            elif key == Key.QR.value:
                user = await User.get_by_id(user_id=msg.from_user.id, session=session)
                if user.status == UserStatus.USER.value:
                    pass
                else:
                    # book - 5772948261 - 20
                    await ut.qr_checking(
                        user_id=msg.from_user.id,
                        key=payloads_list[1],
                        entry_id_str=payloads_list[3],
                        session=session,
                    )
                    return

        except Exception as e:
            log_error(e)

    await ut.get_start_msg(user=msg.from_user, session=session)


# проверяет подписку, в случае удачи пропускает
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.BACK_START.value))
async def back_com_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()

    await ut.get_start_msg(user=cb.from_user, msg_id=cb.message.message_id, session=session)


# Команда начать бронировать
@main_router.message(Command(MenuCommand.BOOK.command))
async def com_book(msg: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await User.get_by_id(user_id=msg.from_user.id, session=session)

    if user and user.status == UserStatus.ADMIN.value:
        await send_start_view_msg(
            chat_id=msg.from_user.id,
            book_type=Key.QR_BOOK.value,
            admin=user,
            session=session,
        )
    else:
        await ut.get_start_book_msg(user=msg.from_user, session=session)


# Команда старт
@main_router.message(Command(MenuCommand.TICKET.command))
async def com_ticket(msg: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await User.get_by_id(user_id=msg.from_user.id, session=session)

    if user.status == UserStatus.ADMIN.value:
        await send_start_view_msg(
            chat_id=msg.from_user.id,
            book_type=Key.QR_TICKET.value,
            admin=user,
            session=session,
        )
    else:
        await send_start_ticket_msg(chat_id=msg.from_user.id, session=session)


# Команда мои брони
@main_router.message(Command(MenuCommand.SETTINGS.command))
async def com_settings(msg: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await User.get_by_id(user_id=msg.from_user.id, session=session)

    if user.status == UserStatus.USER.value:
        await send_main_settings_msg(user_id=msg.from_user.id, session=session)
    else:
        await ut.get_start_msg(user=msg.from_user, session=session)


# показывает кр
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.VIEW_QR.value))
async def book_comment(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    _, type_qr, entry_id_str = cb.data.split(':')
    entry_id = int(entry_id_str)

    if type_qr == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(book_id=entry_id, session=session)
        await cb.message.answer_photo(photo=book.qr_id, caption=ut.get_book_text(book))

    elif type_qr == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(ticket_id=entry_id, session=session)
        await cb.message.answer_photo(photo=ticket.qr_id, caption=ut.get_ticket_text(ticket))


# удаляет сообщение
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.DEL_MSG.value))
async def book_comment(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.delete()
    # _, type_qr, entry_id_str = cb.data.split(':')
    # entry_id = int(entry_id_str)
    #
    # if type_qr == Key.QR_BOOK.value:
    #     book = await Book.get_booking_with_venue(entry_id)
    #     await cb.message.answer_photo(photo=book.qr_id, caption=ut.get_book_text(book))
    #
    # elif type_qr == Key.QR_TICKET.value:
    #     ticket = await Ticket.get_full_ticket(entry_id)
    #     await cb.message.answer_photo(photo=ticket.qr_id, caption=ut.get_ticket_text(ticket))

