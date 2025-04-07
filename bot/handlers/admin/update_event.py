from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime

import asyncio

from .utils import get_main_manage_event_msg
import keyboards as kb
import utils as ut
from google_api import add_book_gs
from db import User, Book, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router
from data import texts_dict
from google_api import create_event_sheet
from enums import AdminCB, UserState, Action, Key, EventData, EventStep, OptionData, event_text_dict


# @admin_route.message(CommandStart())
# async def com_start(msg: Message, state: FSMContext):
#     # await state.clear()
#     print(__name__)


# старт обновления евента
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_UPDATE_1.value))
async def update_event_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    events = await Event.get_all()
    await cb.message.edit_text(f'Выберите мероприятие для изменения', reply_markup=kb.get_update_event_kb(events))


# обновление
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_UPDATE_2.value))
async def update_event_start(cb: CallbackQuery, state: FSMContext):
    _, event_id_str = cb.data.split(':')
    event_id = int(event_id_str)

    # Получаем событие и его опции
    event = await Event.get_event_with_venue(event_id)
    options = await EventOption.get_all(event_id=event_id)

    await state.set_state(UserState.EVENT.value)

    # Преобразуем опции в словари
    options_data = [
        asdict(OptionData(
            id=opt.id,
            name=opt.name,
            place=opt.all_place,
            price=opt.price if opt.price else 0
        )) for opt in options
    ]

    # Формируем EventData
    data_obj = EventData(
        user_id=cb.from_user.id,
        msg_id=cb.message.message_id,
        step=EventStep.END.value,
        content_type=ContentType.TEXT.value,
        venue_id=event.venue.id,
        venue_name=event.venue.name,
        sheet_id=event.venue.event_gs_id,
        event_id=event.id,
        name=event.name,
        text=event.text,
        photo_id=event.photo_id,
        entities=event.entities,
        date_str=event.date_event.strftime(conf.date_format),
        time_str=event.time_event.strftime(conf.time_format),
        options=options_data,
        end=2,
        pade_id=event.gs_page,
    )

    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state)
