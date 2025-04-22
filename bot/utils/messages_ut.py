import asyncio
import typing as t

from aiogram.types import Message, User as AgUser
from aiogram.enums.content_type import ContentType

import keyboards as kb
from init import bot
from db import User, Venue
from enums import UserStatus


# команда старт
async def get_start_msg(user: AgUser, msg_id: int = None) -> None:
    user_info = await User.get_by_id(user.id)

    if user_info.status == UserStatus.USER.value:
        text = (
            f'<b>Привет, {user.full_name}!</b>\n\n'
            f'🔸<i>Выберите действие:</i>'
        )
        markup = kb.get_user_main_kb()
    else:
        text = f'<b>Действия администратора:</b>'
        markup = kb.get_admin_main_kb(user_info.status)

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


# отправляет сообщение всех типов
async def send_any_message(
        chat_id: int,
        text: str,
        entities: list,
        content_type: str,
        media_id: str = None,
        keyboard: kb.InlineKeyboardMarkup = None
) -> t.Optional[Message]:
    if content_type == ContentType.TEXT.value:
        sent = await bot.send_message(
            chat_id=chat_id,
            text=text,
            entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.PHOTO.value:
        sent = await bot.send_photo (
            chat_id=chat_id,
            photo=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.VIDEO.value:
        sent = await bot.send_video (
            chat_id=chat_id,
            video=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.VIDEO_NOTE.value:
        sent = await bot.send_video_note (
            chat_id=chat_id,
            video_note=media_id,
            reply_markup=keyboard
        )

    elif content_type == ContentType.ANIMATION.value:
        sent = await bot.send_animation (
            chat_id=chat_id,
            animation=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.VOICE.value:
        sent = await bot.send_voice (
            chat_id=chat_id,
            voice=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.DOCUMENT.value:
        sent = await bot.send_document (
            chat_id=chat_id,
            voice=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    elif content_type == ContentType.STICKER.value:
        sent = await bot.send_voice (
            chat_id=chat_id,
            voice=media_id,
            caption=text,
            caption_entities=entities,
            reply_markup=keyboard
        )

    else:
        sent = None

    return sent
