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


# старт брони столиков
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_START.value))
async def manage_event_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.EVENT.value)

    data_obj = EventData(
        user_id=cb.from_user.id,
        msg_id=cb.message.message_id,
        step=EventStep.VENUE.value,
        content_type=ContentType.TEXT.value
    )

    venues = await Venue.get_all()
    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=kb.get_event_venue_kb(venues))


async def get_main_manage_event_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = EventData(**data)

    data_obj.print_all()

    if data_obj.end == 1:
        data_obj.end = 2

    elif data_obj.end == 2:
        markup = kb.get_event_end_kb()
        data_obj.end = 0

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


# принимает текстовые поля
@admin_router.message()
async def event_msg_data(msg: Message, state: FSMContext):
    await msg.delete()

    print('tttttttttttttttttttttttttttttttttttttttttt')


# принимает текстовые поля
@admin_router.message(StateFilter(UserState.EVENT.value))
async def event_msg_data(msg: Message, state: FSMContext):
    await msg.delete()

    data = await state.get_data()
    data_obj = EventData(**data)

    if data_obj.step == EventStep.NAME.value:
        data_obj.step = EventStep.COVER.value
        data_obj.name = msg.text[:64]
        markup = kb.get_event_back_kb(AdminCB.EVENT_START.value)

    elif data_obj.step == EventStep.COVER.value:
        entities = msg.entities or msg.caption_entities

        data_obj.step = EventStep.DATE.value
        data_obj.photo_id = msg.photo[-1].file_id if msg.photo else None
        data_obj.text = msg.text or msg.caption
        data_obj.entities = ut.save_entities(entities)
        markup = kb.get_event_date_kb()

    elif data_obj.step == EventStep.DATE.value:
        date_str = ut.hand_date_format(msg.text)
        if not date_str:
            await ut.send_text_alert(chat_id=msg.chat.id, text='❌ Некорректный формат даты')
            return

        data_obj.step = EventStep.TIME.value
        data_obj.date_str = date_str

        if not data_obj.times_list:
            data_obj.times_list = await Event.get_top_times()
        markup = kb.get_event_time_kb(data_obj.times_list)

    elif data_obj.step == EventStep.TIME.value:

        book_time = ut.hand_time_format(msg.text)
        if not book_time:
            await ut.send_text_alert(chat_id=msg.from_user.id, text='❗️ Неверный формат времени')
            return

        data_obj.time_str = book_time
        data_obj.step = EventStep.OPTION_NAME.value

        if data_obj.top_name:
            data_obj.top_name = await EventOption.get_top_names()

        markup = kb.get_event_option_name_kb(data_obj.top_name)

    elif data_obj.step == EventStep.OPTION_NAME.value:
        if data_obj.current_option:
            option_obj = OptionData(**data_obj.current_option)
        else:
            option_obj = OptionData()

        option_obj.name = msg.text[:50]
        data_obj.step = EventStep.OPTION_PLACE.value
        data_obj.current_option = asdict(option_obj)

        if data_obj.top_place:
            data_obj.top_place = await EventOption.get_top_place()

        markup = kb.get_event_option_name_kb(data_obj.top_place)

    elif data_obj.step == EventStep.OPTION_PLACE.value:
        if not msg.text.isdigit():
            await ut.send_text_alert(chat_id=msg.chat.id, text='❌ Неверный формат чисел')
            return

        option_obj = OptionData(**data_obj.current_option)

        option_obj.place = int(msg.text)
        data_obj.step = EventStep.OPTION_PRICE.value
        data_obj.current_option = asdict(option_obj)

        if data_obj.top_price:
            data_obj.top_price = await EventOption.get_top_price()

        markup = kb.get_event_option_name_kb(data_obj.top_place)

    elif data_obj.step == EventStep.OPTION_PRICE.value:
        if not msg.text.isdigit():
            await ut.send_text_alert(chat_id=msg.chat.id, text='❌ Неверный формат чисел')
            return

        option_obj = OptionData(**data_obj.current_option)

        option_obj.price = int(msg.text)
        data_obj.step = EventStep.END.value
        if data_obj.options:
            data_obj.options.append(asdict(option_obj))
        else:
            data_obj.options = [asdict(option_obj)]
        data_obj.current_option = {}

        markup = kb.get_event_end_kb()

    else:
        await ut.send_text_alert(chat_id=msg.from_user.id, text='❗️ Выберите из предложенных вариантов')
        return

    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=markup)


# записывает дату
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_VENUE.value))
async def event_date(cb: CallbackQuery, state: FSMContext):
    _, venue_id_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = EventData(**data)

    if venue_id_str != Action.BACK.value:
        venue_id = int(venue_id_str)

        venue = await Venue.get_by_id(venue_id)
        data_obj.venue_id = venue_id
        data_obj.venue_name = venue.name
        data_obj.sheet_id = venue.event_gs_id

    data_obj.step = EventStep.NAME.value
    await state.update_data(data=asdict(data_obj))

    await get_main_manage_event_msg(state)


# записывает дату
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_DATE.value))
async def event_date(cb: CallbackQuery, state: FSMContext):
    _, date_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = EventData(**data)

    if date_str != Action.BACK.value:
        data_obj.date_str = date_str

        if not data_obj.times_list:
            data_obj.times_list = await Event.get_top_times()

    data_obj.step = EventStep.TIME.value
    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=kb.get_event_time_kb(data_obj.times_list))


# записывает дату
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_TIME.value))
async def event_time(cb: CallbackQuery, state: FSMContext):
    _, time_str = cb.data.split(':')

    time_str = time_str.replace(' ', ':')
    data = await state.get_data()
    data_obj = EventData(**data)

    if time_str != Action.BACK.value:
        data_obj.time_str = time_str

    if data_obj.top_name:
        data_obj.top_name = await EventOption.get_top_names()

    data_obj.step = EventStep.OPTION_NAME.value
    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=kb.get_event_option_name_kb(data_obj.top_name))


# обновляет данные
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_EDIT.value))
async def event_edit(cb: CallbackQuery, state: FSMContext):
    _, step = cb.data.split(':')

    data = await state.get_data()
    data_obj = EventData(**data)

    data_obj.step = step
    data_obj.end = 1

    # Роутинг по шагам
    if step == EventStep.VENUE.value:
        venues = await Venue.get_all()
        markup = kb.get_event_venue_kb(venues)

    elif step == EventStep.NAME.value:
        markup = kb.get_event_back_kb(AdminCB.EVENT_START.value)

    elif step == EventStep.COVER.value:
        markup = kb.get_event_back_kb(AdminCB.EVENT_START.value)

    elif step == EventStep.DATE.value:
        markup = kb.get_event_date_kb()

    elif step == EventStep.TIME.value:
        if not data_obj.times_list:
            data_obj.times_list = await Event.get_top_times()
        markup = kb.get_event_time_kb(data_obj.times_list)

    elif step == EventStep.OPTION_NAME.value:
        if not data_obj.top_name:
            data_obj.top_name = await EventOption.get_top_names()
        markup = kb.get_event_option_name_kb(data_obj.top_name)

    elif step == EventStep.OPTION_PLACE.value:
        if not data_obj.top_place:
            data_obj.top_place = await EventOption.get_top_place()
        markup = kb.get_event_option_name_kb(data_obj.top_place)

    elif step == EventStep.OPTION_PRICE.value:
        if not data_obj.top_price:
            data_obj.top_price = await EventOption.get_top_price()
        markup = kb.get_event_option_name_kb(data_obj.top_price)

    else:
        markup = None

    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=markup)


# записывает опции
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_TIME.value))
async def event_time(cb: CallbackQuery, state: FSMContext):
    _, cb_value = cb.data.split(':')

    data = await state.get_data()
    data_obj = EventData(**data)

    if data_obj.current_option:
        option_obj = OptionData(**data_obj.current_option)
    else:
        option_obj = OptionData()

    if data_obj.step == EventStep.OPTION_NAME.value:
        option_obj.name = cb_value
        data_obj.step = EventStep.OPTION_PLACE.value
        data_obj.current_option = asdict(option_obj)

        if data_obj.top_place:
            data_obj.top_place = await EventOption.get_top_place()

        markup = kb.get_event_option_name_kb(data_obj.top_place)

    elif data_obj.step == EventStep.OPTION_PLACE.value:
        option_obj.place = int(cb_value)
        data_obj.step = EventStep.OPTION_PRICE.value
        data_obj.current_option = asdict(option_obj)

        if data_obj.top_price:
            data_obj.top_price = await EventOption.get_top_price()

        markup = kb.get_event_option_name_kb(data_obj.top_place)

    elif data_obj.step == EventStep.OPTION_PRICE.value:
        option_obj.price = int(cb_value)
        data_obj.step = EventStep.END.value
        if data_obj.options:
            data_obj.options.append(asdict(option_obj))
        else:
            data_obj.options = [asdict(option_obj)]
        data_obj.current_option = {}

        markup = kb.get_event_end_kb()

    else:
        data_obj.current_option = {}
        data_obj.step = EventStep.END.value
        markup = None

    await state.update_data(data=asdict(data_obj))
    await get_main_manage_event_msg(state, markup=markup)


# сохраняет ивент
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_END.value))
async def event_end(cb: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    await state.clear()
    data_obj = EventData(**data)

    #     сохраняем ивент
    event_id = await Event.add(
        creator_id=cb.from_user.id,  # например, из Telegram user.id
        venue_id=data_obj.venue_id,  # передаётся отдельно
        time_event=datetime.strptime(data_obj.time_str, conf.time_format).time(),
        date_event=datetime.strptime(data_obj.date_str, conf.date_format).date(),
        name=data_obj.name,
        text=data_obj.text,
        entities=data_obj.entities,
        photo_id=data_obj.photo_id
    )
    #     сохраняем опции
    for option_dict in data_obj.options or []:
        option = OptionData(**option_dict)  # преобразуем словарь в dataclass

        await EventOption.add(
            event_id=event_id,
            name=option.name,
            all_place=option.place,
            price=option.price if option.price is not None else 0
        )

#     сохраняем записывем в таблицу
    page_name = f'{data_obj.date_str[:-5]} {data_obj.name}'[:100]
    await create_event_sheet(
        spreadsheet_id=data_obj.sheet_id,
        sheet_name=page_name,
        options=data_obj.options
    )
    #     Отчитываемся об успехе
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(text='✅ Мероприятие успешно создано')

