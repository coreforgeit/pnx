from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime

import asyncio

from .utils import send_main_manage_event_msg
import keyboards as kb
import utils as ut
from db import User, Book, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router
from data import texts_dict
from google_api import create_event_sheet
from enums import AdminCB, UserState, Action, Key, EventData, EventStep, OptionData, event_text_dict


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
    await send_main_manage_event_msg(state, markup=kb.get_event_venue_kb(venues))


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

        if not data_obj.top_name:
            data_obj.top_name = await EventOption.get_top_names()

        markup = kb.get_event_option_select_kb(data_obj.top_name)

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

        markup = kb.get_event_option_select_kb(data_obj.top_place)

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

        markup = kb.get_event_option_select_kb(data_obj.top_price)

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

        markup = kb.get_event_end_kb(data_obj.event_id)

    else:
        await ut.send_text_alert(chat_id=msg.from_user.id, text='❗️ Выберите из предложенных вариантов')
        return

    await state.update_data(data=asdict(data_obj))
    await send_main_manage_event_msg(state, markup=markup)


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

    await send_main_manage_event_msg(state)


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
    await send_main_manage_event_msg(state, markup=kb.get_event_time_kb(data_obj.times_list))


# записывает время
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_TIME.value))
async def event_time(cb: CallbackQuery, state: FSMContext):
    _, time_str = cb.data.split(':')

    time_str = time_str.replace(' ', ':')
    data = await state.get_data()
    data_obj = EventData(**data)

    if time_str != Action.BACK.value:
        data_obj.time_str = time_str

    if not data_obj.top_name:
        data_obj.top_name = await EventOption.get_top_names()

    data_obj.step = EventStep.OPTION_NAME.value
    await state.update_data(data=asdict(data_obj))
    await send_main_manage_event_msg(state, markup=kb.get_event_option_select_kb(data_obj.top_name))


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
        markup = kb.get_event_option_select_kb(data_obj.top_name)

    # elif step == EventStep.OPTION_PLACE.value:
    #     if not data_obj.top_place:
    #         data_obj.top_place = await EventOption.get_top_place()
    #     markup = kb.get_event_option_select_kb(data_obj.top_place)
    #
    # elif step == EventStep.OPTION_PRICE.value:
    #     if not data_obj.top_price:
    #         data_obj.top_price = await EventOption.get_top_price()
    #     markup = kb.get_event_option_select_kb(data_obj.top_price)

    elif step == EventStep.OPTION_DEL.value:
        markup = kb.get_event_option_del_kb(data_obj.options)

    else:
        markup = None

    await state.update_data(data=asdict(data_obj))
    await send_main_manage_event_msg(state, markup=markup)


# записывает опции
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_OPTION.value))
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

        if not data_obj.top_place:
            data_obj.top_place = await EventOption.get_top_place()

        markup = kb.get_event_option_select_kb(data_obj.top_place)

    elif data_obj.step == EventStep.OPTION_PLACE.value:
        option_obj.place = int(cb_value)
        data_obj.step = EventStep.OPTION_PRICE.value
        data_obj.current_option = asdict(option_obj)

        if not data_obj.top_price:
            data_obj.top_price = await EventOption.get_top_price()

        markup = kb.get_event_option_select_kb(data_obj.top_price)

    elif data_obj.step == EventStep.OPTION_PRICE.value:
        option_obj.price = int(cb_value)
        data_obj.step = EventStep.END.value
        if data_obj.options:
            data_obj.options.append(asdict(option_obj))
        else:
            data_obj.options = [asdict(option_obj)]
        data_obj.current_option = {}

        markup = kb.get_event_end_kb(data_obj.event_id)

    elif data_obj.step == EventStep.OPTION_DEL.value:
        opt_index = int(cb_value)
        data_obj.options.pop(opt_index)
        data_obj.step = EventStep.END.value

        markup = kb.get_event_end_kb(data_obj.event_id)

    else:
        data_obj.current_option = {}
        data_obj.step = EventStep.END.value
        markup = None

    await state.update_data(data=asdict(data_obj))
    await send_main_manage_event_msg(state, markup=markup)


# сохраняет ивент
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.EVENT_END.value))
async def event_end(cb: CallbackQuery, state: FSMContext):
    sent = await cb.message.answer('⏳')

    data = await state.get_data()
    data_obj = EventData(**data)

    try:
        #     сохраняем ивент
        event_id = await Event.add(
            creator_id=cb.from_user.id,  # например, из Telegram user.id
            venue_id=data_obj.venue_id,  # передаётся отдельно
            time_event=datetime.strptime(data_obj.time_str, conf.time_format).time(),
            date_event=datetime.strptime(data_obj.date_str, conf.date_format).date(),
            name=data_obj.name,
            text=data_obj.text,
            entities=data_obj.entities,
            photo_id=data_obj.photo_id,
            event_id=data_obj.event_id
        )
        #     сохраняем опции
        updated_options = []

        for option_dict in data_obj.options or []:
            option = OptionData(**option_dict)  # преобразуем словарь в dataclass

            option_id = await EventOption.add(
                event_id=event_id,
                name=option.name,
                all_place=option.place,
                price=option.price if option.price is not None else 0,
                option_id=option.id
            )

            option.id = option_id
            updated_options.append(asdict(option))

    #     сохраняем записывем в таблицу
        page_name = f'{data_obj.date_str[:-5]} {data_obj.name}'[:100]
        page_id = await create_event_sheet(
            spreadsheet_id=data_obj.sheet_id,
            sheet_name=page_name,
            options=updated_options,
            page_id=data_obj.pade_id
        )

        await Event.update(event_id=event_id, page_id=page_id)
        #     Отчитываемся об успехе
        await cb.message.edit_reply_markup(reply_markup=None)
        await state.clear()

        await sent.edit_text(text='✅ Мероприятие успешно создано')

    except Exception as e:
        log_error(e)
        await sent.edit_text(text=f'❌ Не удалось сохранить мероприятие\n\nОшибка:\n{e}')

