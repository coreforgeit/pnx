from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from uuid import uuid4
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from .user_utils import send_main_ticket_msg, send_start_ticket_msg, send_selected_event_msg
from db import Ticket, Event, EventOption, Venue, AdminLog
from settings import conf, log_error
from init import user_router, bot
from google_api import add_ticket_row_to_registration, update_book_status_gs
from enums import (
    UserCB, AdminCB, BookStatus, TicketData, TicketStep, UserState, Action, Key, AdminAction, TicketRedisData
)


# старт билеты
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_START.value))
async def ticket_start(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')

    await state.clear()
    await send_start_ticket_msg(
        chat_id=cb.from_user.id,
        # msg_id=cb.message.message_id if action == Action.BACK.value else None,
        msg_id=cb.message.message_id,
    )


# сохраняем ивент, спрашиваем опции
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_EVENT.value))
async def ticket_event(cb: CallbackQuery, state: FSMContext):
    _, event_id_str = cb.data.split(':')

    if event_id_str != Action.BACK.value:
        event_id = int(event_id_str)
    else:
        data = await state.get_data()
        data_obj = TicketData(**data)
        event: Event = data_obj.event
        event_id = event.id

    await cb.message.delete()
    await send_selected_event_msg(chat_id=cb.from_user.id, event_id=event_id)


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
        # option = EventOption(**data_obj.option)
        option: EventOption = data_obj.option

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
    option_selected: EventOption = data_obj.option
    option_actual = await EventOption.get_by_id(option_selected.id)

    # если места закончились, пока шло бронирование
    if not option_actual or data_obj.count_place > option_actual.empty_place:
        empty_place = option_actual.empty_place if option_actual else 0
        text = f'❗️ К сожалению осталось только {empty_place} мест'
        await ut.send_text_alert(chat_id=cb.from_user.id, text=text)
        return

    await cb.message.edit_reply_markup(reply_markup=None)
    amount = option_actual.price * data_obj.count_place

    ticket_id_list = []
    last_row = await Ticket.get_max_event_row(event.id)
    venue = await Venue.get_by_id(event.venue_id)

    # сохраняем билеты
    ofd_items = []
    for i in range(0, data_obj.count_place):
        try:
            await cb.message.edit_text(
                f'<b>⏳ Обрабатываем заявку, нам нужно немного времени</b>\n'
                f'<i>🔹Осталось: {data_obj.count_place - i}</i>'
            )
        except Exception as e:
            pass

        ticket_id = await Ticket.add(
            event_id=event.id,
            user_id=cb.from_user.id,
            option_id=option_actual.id,
            status=BookStatus.NEW.value,
            is_active=False
        )
        ticket_id_list.append(ticket_id)

        row = await add_ticket_row_to_registration(
            spreadsheet_id=venue.event_gs_id,
            page_id=event.gs_page,
            ticket_id=ticket_id,
            option_name=option_actual.name,
            user_name=cb.from_user.full_name,
            start_row=last_row,
            status=BookStatus.NEW.value
        )

        last_row = row + 1
        await Ticket.update(
            ticket_id=ticket_id,
            gs_sheet=venue.event_gs_id,
            gs_page=event.gs_page,
            gs_row=row
        )

        price_tian = option_actual.price * 100
        ofd_items.append(
            {
                "vat": 12,
                "price": price_tian,
                "qty": 1,
                "name": f"Ticket-{ticket_id}",
                "package_code": f'{ticket_id}',
                "mxik": "10202001002000000",
                "total": price_tian
            }
        )

    # уменьшить количество мест
    await EventOption.update(option_id=option_actual.id, add_place=0 - data_obj.count_place)
    # возвращение статуса по таймеру
    ut.create_cancel_ticket(user_id=cb.from_user.id, ticket_id_list=ticket_id_list)

    if amount:
        redis_data = {
            'user_id': cb.from_user.id,
            'full_name': cb.from_user.full_name,
            'ticket_id_list': ticket_id_list,
            'data': ofd_items
        }
        invoice_id = ut.save_redis_temp(key=Key.PAY_DATA.value, data=redis_data)
        invoice_link = await ut.create_invoice(
            invoice_id=invoice_id,
            amount=amount,
            ofd_items=ofd_items
        )
        data_obj.ticket_id_list = ticket_id_list
        await state.update_data(data=asdict(data_obj))

        await cb.message.edit_text(
            '<b>Выберите способ оплаты:</b>', reply_markup=kb.get_ticket_pay_method_kb(invoice_link)
        )

    else:
        await state.clear()
        await ut.confirm_tickets(
            user_id=cb.from_user.id, full_name=cb.from_user.full_name, ticket_id_list=ticket_id_list
        )


# альтернативная оплата
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.TICKET_ALTER_PAY_1.value))
async def ticket_alter_pay(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    data_obj = TicketData(**data)
    event: Event = data_obj.event
    option_selected: EventOption = data_obj.option
    option_actual = await EventOption.get_by_id(option_selected.id)

    # если места закончились, пока шло бронирование
    # if not option_actual or data_obj.count_place > option_actual.empty_place:
    #     empty_place = option_actual.empty_place if option_actual else 0
    #     text = f'❗️ К сожалению осталось только {empty_place} мест'
    #     await ut.send_text_alert(chat_id=cb.from_user.id, text=text)
    #     return

    amount = option_actual.price * data_obj.count_place
    venue = await Venue.get_by_id(event.venue_id)

    # напоминалки
    # ut.create_cancel_ticket(cb.from_user.id, data_obj.ticket_id_list)
    redis_data = TicketRedisData(
        ticket_id_list=data_obj.ticket_id_list,
        event_id=event.id,
        option_id=option_actual.id,
        user_id=cb.from_user.id,
        full_name=cb.from_user.full_name,
    )
    # redis_data = {
    #     'ticket_id_list': data_obj.ticket_id_list,
    #     'event_id': event.id,
    #     'user_id': cb.from_user.id,
    #     'full_name': cb.from_user.full_name,
    # }
    redis_hash = ut.save_redis_data(key=Key.QR_TICKET.value, data=asdict(redis_data))

    username_text = f'(@{cb.from_user.username})' if cb.from_user.username else ''
    text = (
        f'<b>💸 Заявка на билеты</b>\n\n'
        f'Пользователь: {cb.from_user.full_name} {username_text}\n'
        f'Заведение: {venue.name}\n'
        f'Опции: {option_selected.name}\n'
        f'Количество: {data_obj.count_place}\n'
        f'Стоимость: {amount}\n'
    )

    await bot.send_message(
        chat_id=venue.admin_chat_id,
        text=text,
        reply_markup=kb.get_ticket_pay_confirm_kb(ticket_id=data_obj.ticket_id_list[0], redis_key=redis_hash)
    )

    await cb.message.answer(text='<b>✅ Заявка принята. В ближайшее время с вами свяжется администратор</b>')


# альтернативная оплата
@user_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ALTER_PAY.value))
async def ticket_alter_pay(cb: CallbackQuery, state: FSMContext):
    _, action, redis_hash = cb.data.split(':')

    redis_key = f'{Key.QR_TICKET.value}-{redis_hash}'
    redis_data_raw = ut.get_redis_data(key=redis_key)
    redis_data = TicketRedisData(**redis_data_raw)

    if conf.debug:
        redis_data.print_all()

    if action == Action.CONF.value:
        # redis_data = ut.get_redis_data(key=redis_key)
        await ut.confirm_tickets(
            user_id=redis_data.user_id,
            full_name=redis_data.full_name,
            ticket_id_list=redis_data.ticket_id_list,
        )
        action_text = '✅ Подтвердил'
        admin_action = AdminAction.PAY_CONFIRMED.value

    elif action == Action.DEL.value:

        action_text = '❌ Отменил'
        admin_action = AdminAction.PAY_CANCELED.value

        for ticket_id in redis_data.ticket_id_list:
            ticket = await Ticket.get_full_ticket(ticket_id)
            if ticket.status == BookStatus.NEW.value:
                await Ticket.update(ticket_id=ticket.id, status=BookStatus.CANCELED.value, is_active=False)

                await update_book_status_gs(
                    spreadsheet_id=ticket.event.venue.event_gs_id,
                    sheet_name=ticket.event.gs_page,
                    status=BookStatus.CANCELED.value,
                    row=ticket.gs_row,
                    book_type=Key.QR_TICKET.value
                )

                ticket_text = ut.get_ticket_text(ticket)
                text = f'<b>❌ Билет аннулирован администратором</b>\n{ticket_text}'
                await bot.send_message(chat_id=redis_data.user_id, text=text)
                
        await EventOption.update(option_id=redis_data.option_id, add_place=len(redis_data.ticket_id_list))

    else:
        await cb.message.answer(f'<b>❌ Ошибка запроса</b>')
        return

    ut.del_redis_data(redis_key)
    await cb.message.edit_text(
        f'{cb.message.text}\n\n<b>{action_text} {cb.from_user.full_name}</b>'
    )
    await AdminLog.add(
        admin_id=cb.from_user.id,
        user_id=redis_data.user_id,
        action=admin_action,
        comment=cb.message.text
    )

