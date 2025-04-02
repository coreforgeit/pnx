import asyncio

from aiogram.types import Message, User as AgUser

import keyboards as kb
from init import bot
from db import User, Venue
from enums import UserStatus


# команда старт
async def get_start_msg(user: AgUser, msg_id: int = None) -> None:
    user_info = await User.get_by_id(user.id)

    print(user.id)
    print(user_info)
    print(type(user_info))
    print(user_info.status)

    if user_info.status == UserStatus.USER.value:
        text = (
            f'<b>Привет, {user.full_name}!</b>\n\n'
            f'🔸<i>Выберите действие:</i>'
        )
        markup = kb.get_user_main_kb()
    else:
        text = (
            f'<b>Действия администратора:</b>\n\n'
        )
        markup = kb.get_user_main_kb()

    if msg_id:
        await bot.edit_message_text(chat_id=user.id, message_id=msg_id, text=text, reply_markup=markup)

    else:
        await bot.send_message(chat_id=user.id, text=text, reply_markup=markup)


# начать бронирование
async def get_start_book_msg(user: AgUser, msg_id: int = None) -> None:
    text = f'<b>Где бы вы хотели забронировать столик?</b>'
    venues = await Venue.get_all()
    markup = kb.get_book_main_kb(venues)

    if msg_id:
        await bot.edit_message_text(chat_id=user.id, message_id=msg_id, text=text, reply_markup=markup)

    else:
        await bot.send_message(chat_id=user.id, text=text, reply_markup=markup)


# отправляет и удаляет предупреждение
async def send_text_alert(chat_id: int, text: str) -> None:
    sent = await bot.send_message(chat_id=chat_id, text=text)
    await asyncio.sleep(3)
    await sent.delete()