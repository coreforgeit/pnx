from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from .user_utils import send_main_ticket_msg, send_start_ticket_msg
from db import Ticket, Event, EventOption, Venue
from settings import conf, log_error
from init import user_router, bot
from google_api import add_ticket_row_to_registration
from enums import UserCB, BookStatus, TicketData, TicketStep, ticket_text_dict, UserState, Action, Key


# старт билеты
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_START.value))
async def ticket_start(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')

    await state.clear()
    await send_start_ticket_msg(
        chat_id=cb.from_user.id,
        msg_id=cb.message.message_id if action == Action.BACK.value else None,
    )


# сохраняем ивент, спрашиваем опции
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_EVENT.value))
async def ticket_event(cb: CallbackQuery, state: FSMContext):
    _, event_id_str = cb.data.split(':')
    event_id = int(event_id_str)

    await cb.message.delete()

    event = await Event.get_by_id(event_id)
    options = await EventOption.get_all(event_id=event_id)

    markup = kb.get_ticket_options_kb(options)
    entities = ut.recover_entities(event.entities)

    if event.photo_id:
        await cb.message.answer_photo(
            photo=event.photo_id,
            caption=event.text,
            caption_entities=entities,
            parse_mode=None,
            reply_markup=markup
        )

    else:
        await cb.message.answer(
            text=event.text,
            entities=entities,
            parse_mode=None,
            disable_web_page_preview=True,
            reply_markup=markup
        )


    # if event_id_str != Action.BACK.value:
    #     event_id = int(event_id_str)
    #
    #     data_obj = TicketData()
    #     event = await Event.get_by_id(event_id)
    #
    #     data_obj.event = event
    #
    # else:
    #     data = await state.get_data()
    #     data_obj = TicketData(**data)
    #     event = Event(**data_obj.event)
    #
    # data_obj.step = TicketStep.OPTION.value
    # await state.update_data(data=asdict(data_obj))
    # await get_main_ticket_msg(state, markup=kb.get_ticket_options_kb(options))


@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_PLACE.value))
async def ticket_place(cb: CallbackQuery, state: FSMContext):
    _, option_id_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = TicketData(**data)

    if option_id_str != Action.BACK.value:
        option_id = int(option_id_str)

        await state.set_state(UserState.TICKET.value)
        # data_obj = TicketData()

        option = await EventOption.get_by_id(option_id)
        event = await Event.get_by_id(option.event_id)
        data_obj.option = option
        data_obj.event = event

        data_obj.user_id = cb.from_user.id
        data_obj.step = TicketStep.COUNT.value

        await state.update_data(data=asdict(data_obj))

    else:
        option = EventOption(**data_obj.option)

    data_obj.step = TicketStep.COUNT.value

    await state.update_data(data=asdict(data_obj))
    await send_main_ticket_msg(state, markup=kb.get_ticket_place_kb(option.empty_place))


@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_CONFIRM.value))
async def ticket_check(cb: CallbackQuery, state: FSMContext):
    _, place_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = TicketData(**data)

    if place_str != Action.BACK.value:
        # place = int(place_str)
        data_obj.msg_id = cb.message.message_id
        data_obj.count_place = int(place_str)

    data_obj.step = TicketStep.CONFIRM.value

    await state.update_data(data=asdict(data_obj))
    await send_main_ticket_msg(state, markup=kb.get_ticket_confirm_kb())


@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_END.value))
async def ticket_end(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    data_obj = TicketData(**data)
    event: Event = data_obj.event
    option_old: EventOption = data_obj.option
    option = await EventOption.get_by_id(option_old.id)

    # если места закончились, пока шло бронирование
    if not option or data_obj.count_place > option.empty_place:
        empty_place = option.empty_place if option else 0
        text = f'❗️ К сожалению осталось только {empty_place} мест'
        await ut.send_text_alert(chat_id=cb.from_user.id, text=text)
        return

    await state.clear()

    amount = option.price * data_obj.count_place
    amount = 0

    if amount:
        await cb.message.answer('Тут идём к оплате')

    else:
        venue = await Venue.get_by_id(event.venue_id)
        for i in range(0, data_obj.count_place):
            ticket_id = await Ticket.add(
                event_id=event.id,
                user_id=cb.from_user.id,
                option_id=option.id,
                status=BookStatus.CONFIRMED.value
            )
            qr_data = f'{Key.QR_TICKET.value}:{cb.from_user.id}:{ticket_id}'
            text = (
                f'<b>{event.name}\n'
                f'📍 {venue.name}\n'
                f'⏰ {event.date_str()} {event.time_str()}\n'
                f'🪑 {option.name}</b>'
            )
            await ut.generate_and_sand_qr(chat_id=cb.from_user.id, qr_data=qr_data, caption=text)
            last_row = await Ticket.get_max_event_row(event.id)

            #     записать в таблицу
            await add_ticket_row_to_registration(
                spreadsheet_id=venue.event_gs_id,
                page_id=event.gs_page,
                ticket_id=ticket_id,
                option_name=option.name,
                user_name=cb.from_user.full_name,
                start_row=last_row
            )

        # уменьшить количество мест
        await EventOption.update(option_id=option.id, add_place=0 - data_obj.count_place)

        text = f'<b>Продано {data_obj.count_place} билета на {event.name}</b>'

        await bot.send_message(chat_id=conf.admin_chat, text=text)
        # await bot.send_message(chat_id=venue.admin_chat_id, text=text)
