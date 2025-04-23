from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime

import asyncio
import random

from .admin_utils import sent_mailing_preview
import keyboards as kb
import utils as ut
from db import User, AdminLog, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router
from data import texts_dict
from google_api import create_event_sheet
from enums import AdminCB, UserState, Action, AdminAction, MailingData


# старт рассылки
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.MAILING_START.value))
async def mailing_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()

    await state.clear()
    await state.set_state(UserState.MAILING.value)

    await sent_mailing_preview(chat_id=cb.from_user.id, state=state, markup=kb.get_back_start_kb())


# предпросмотр сообщения
@admin_router.message(StateFilter(UserState.MAILING.value))
async def mailing_preview(msg: Message, state: FSMContext):
    data = await state.get_data()
    data_obj = MailingData(**data)

    if data_obj.del_msg_id:
        try:
            await bot.delete_message(chat_id=msg.chat.id, message_id=data_obj.del_msg_id)
            data_obj.del_msg_id = None
            await state.update_data(data=asdict(data_obj))

        except Exception as e:
            log_error(e)

    await sent_mailing_preview(chat_id=msg.chat.id, state=state, msg=msg, markup=kb.get_mailing_send_kb())


# подтверждение рассылки
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.MAILING_1.value))
async def mailing_1(cb: CallbackQuery, state: FSMContext):

    users = await User.get_all_users(for_mailing=True)
    text = (
        f'Будет отправлено {len(users)} сообщений\n\n'
        f'Нажмите "📲 Подтвердить отправку", чтоб начать рассылку'
    )

    await cb.answer(text, show_alert=True)
    await cb.message.edit_reply_markup(reply_markup=kb.get_mailing_send_kb(True))


# рассылка
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.MAILING_2.value))
async def mailing_2(cb: CallbackQuery, state: FSMContext):
    _, action = cb.data.split(':')
    await state.clear()

    if action == Action.DEL.value:
        await cb.message.delete()
        await ut.get_start_msg(user=cb.from_user)
        return

    users = await User.get_all_users(for_mailing=True)
    count_users = len(users)

    text = (
        f'<b>⏳ Рассылка</b>\n'
        f'Отправлено 0 из {count_users}'
    )
    sent = await cb.message.answer(text)
    c = 0
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user.id,
                from_chat_id=cb.message.chat.id,
                message_id=cb.message.message_id,
                parse_mode=None,
            )
            c += 1
            if random.randint(0, 50) == 30:
                text = (
                    f'<b>⏳ Рассылка</b>\n'
                    f'Отправлено {c} из {count_users}'
                )
                await sent.edit_text(text)
        except Exception as e:
            log_error(e, wt=False)

    text = (
        f'<b>✅ Рассылка завершена</b>\n'
        f'Отправлено {c} из {count_users}'
    )
    await sent.edit_text(text)
    await cb.message.edit_reply_markup(reply_markup=None)

    # запись в журнал
    text = cb.message.text or cb.message.caption
    if not text:
        text = cb.message.content_type
    await AdminLog.add(
        admin_id=cb.from_user.id, action=AdminAction.MAILING.value, comment=text
    )
