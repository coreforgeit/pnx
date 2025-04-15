from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime

import asyncio

import db
import keyboards as kb
import utils as ut
from db import User, Book, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router
from data import texts_dict
from google_api import create_event_sheet
from enums import AdminCB, UserState, Action, Key, EventData, EventStep, OptionData, event_text_dict


# сообщение для изменения ивента
async def get_main_manage_event_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = EventData(**data)

    data_obj.print_all()

    if data_obj.end and not data_obj.step.startswith('option'):
        if data_obj.end == 1:
            data_obj.end = 2

        elif data_obj.end == 2:
            markup = kb.get_event_end_kb(data_obj.event_id)
            data_obj.end = 0
            data_obj.step = EventStep.END.value

        await state.update_data(data=asdict(data_obj))

    if data_obj.options:
        option_text = '\nОпции:\n'
        options: list[dict] = data_obj.options
        for option in options:
            option_obj = OptionData(**option)
            option_text += f'{option_obj.name} {option_obj.place} мест {option_obj.price} UZS\n'

    else:
        option_text = ''

    if data_obj.current_option:
        option_obj = OptionData(**data_obj.current_option)
        option_text += f'\n{option_obj.name} {option_obj.place} мест {option_obj.price} UZS\n'.replace('None', ' ')

    row_list = [
        f'{data_obj.venue_name}\n\n',
        f'{data_obj.name}\n',
        f'Дата: {data_obj.date_str}\n',
        f'Время: {data_obj.time_str}\n',
    ]
    bottom_text = ''.join(row for row in row_list if 'None' not in row).strip()

    text = f'{data_obj.text}\n\n--------\n{bottom_text}{option_text}\n\n{event_text_dict.get(data_obj.step)}'
    entities = ut.recover_entities(data_obj.entities)

    if data_obj.content_type == ContentType.TEXT.value and not data_obj.photo_id:
        await bot.edit_message_text(
            chat_id=data_obj.user_id,
            message_id=data_obj.msg_id,
            text=text,
            entities=entities,
            parse_mode=None,
            reply_markup=markup
        )

    elif data_obj.content_type == ContentType.TEXT.value and data_obj.photo_id:
        await bot.delete_message(chat_id=data_obj.user_id, message_id=data_obj.msg_id)

        sent = await bot.send_photo(
            chat_id=data_obj.user_id,
            photo=data_obj.photo_id,
            caption=text,
            caption_entities=entities,
            parse_mode=None,
            reply_markup=markup
        )

        data_obj.msg_id = sent.message_id
        data_obj.content_type = sent.content_type
        await state.update_data(data=asdict(data_obj))

    elif data_obj.content_type == ContentType.PHOTO.value and not data_obj.photo_id:
        await bot.delete_message(chat_id=data_obj.user_id, message_id=data_obj.msg_id)

        sent = await bot.send_message(
            chat_id=data_obj.user_id,
            text=text,
            entities=entities,
            parse_mode=None,
            reply_markup=markup
        )

        data_obj.msg_id = sent.message_id
        data_obj.content_type = sent.content_type
        await state.update_data(data=asdict(data_obj))

    elif data_obj.content_type == ContentType.PHOTO.value and data_obj.photo_id:

        media = InputMediaPhoto(
            media=data_obj.photo_id,
            caption=text,
            caption_entities=entities,
            parse_mode=None
        )
        await bot.edit_message_media(
            chat_id=data_obj.user_id,
            message_id=data_obj.msg_id,
            media=media,
            reply_markup=markup
        )