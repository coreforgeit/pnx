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
async def group_msg(msg: Message):
    venue = await Venue.get_by_admin_chat(chat_id=int(msg.text))
    if venue:
        await Venue.update(venue_id=venue.id, chat_id=msg.chat.id)
        text = f'✅ Чат успешно добавлен как группа для заведения {venue.name}'
        await msg.answer(text)


# Команда старт
@main_router.message(CommandStart())
async def com_start(msg: Message, state: FSMContext):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)
    print(f'msg.text: {msg.text}')
    payloads = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else None
    # print(msg.text)
    # print(payloads)

    if payloads:
        try:
            # print(f'msg.text: {msg.text}')
            print(f'payloads: {payloads}')
            # payloads: qr-book-5772948261-20
            payloads_list = payloads.split('-')
            key = payloads_list[0]
            # key, value = payloads.split('-') if len(payloads.split('-')) == 2 else (None, 0)

            if key == Key.ADD_ADMIN.value:
                value = payloads_list[1]
                key = f"{Key.ADD_ADMIN.value}{value}"
                admin_data = ut.get_redis_data(key, del_data=True)

                if not admin_data:
                    await msg.answer('⚠️ Ссылка устарела или уже была использована')

                else:
                    await User.update(
                        user_id=msg.from_user.id,
                        status=admin_data['user_status'],
                        venue_id=admin_data['venue_id'],
                    )
                    await msg.answer('✅ Статус обновлён')

            elif key == Key.QR_TICKET.value:
                value = payloads_list[1]
                event_id = int(value)
                await send_selected_event_msg(chat_id=msg.from_user.id, event_id=event_id)
                return

            elif key == Key.QR.value:
                user = await User.get_by_id(msg.from_user.id)
                if user.status == UserStatus.USER.value:
                    pass
                else:
                    # book - 5772948261 - 20
                    await ut.qr_checking(user_id=msg.from_user.id, key=payloads_list[1], entry_id_str=payloads_list[3])
                    return

        except Exception as e:
            log_error(e)

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
    user = await User.get_by_id(msg.from_user.id)

    if user.status == UserStatus.USER.value:
        await ut.get_start_book_msg(user=msg.from_user)
    else:
        await send_start_view_msg(chat_id=msg.from_user.id, book_type=Key.QR_BOOK.value, admin=user)


# Команда старт
@main_router.message(Command(MenuCommand.TICKET.command))
async def com_ticket(msg: Message, state: FSMContext):
    await state.clear()
    user = await User.get_by_id(msg.from_user.id)

    if user.status == UserStatus.USER.value:
        await send_start_ticket_msg(chat_id=msg.from_user.id)
    else:
        await send_start_view_msg(chat_id=msg.from_user.id, book_type=Key.QR_TICKET.value, admin=user)


# Команда мои брони
@main_router.message(Command(MenuCommand.SETTINGS.command))
async def com_settings(msg: Message, state: FSMContext):
    await state.clear()
    user = await User.get_by_id(msg.from_user.id)

    if user.status == UserStatus.USER.value:
        await send_main_settings_msg(msg.from_user.id)
    else:
        await ut.get_start_msg(user=msg.from_user)


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

