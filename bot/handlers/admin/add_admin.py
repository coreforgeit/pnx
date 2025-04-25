from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from aiogram import Router
from aiogram.enums.content_type import ContentType
from dataclasses import asdict
from datetime import datetime
from uuid import uuid4

import asyncio

import keyboards as kb
import utils as ut
from db import User, Ticket, Book, EventOption, AdminLog, Venue
from settings import conf, log_error
from init import bot, admin_router, redis_client
from enums import AdminCB, UserState, Action, Key, SendData, UserStatus, AdminAction


# старт просмотра броней
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_START.value))
async def add_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    text = f'<b>Выберите заведение:</b>'
    venues = await Venue.get_all()

    await cb.message.edit_text(text=text, reply_markup=kb.get_event_venue_kb(
        venues=venues,
        cb=AdminCB.ADD_VENUE.value
    ))


# старт просмотра броней
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_VENUE.value))
async def add_venue(cb: CallbackQuery, state: FSMContext):
    _, venue_id_str = cb.data.split(':')
    venue_id = int(venue_id_str)

    text = f'<b>Укажите статус пользователя:</b>'
    await cb.message.edit_text(text=text, reply_markup=kb.get_add_admin_status_kb(venue_id=venue_id))


# старт просмотра броней
@admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_STATUS.value))
async def add_status(cb: CallbackQuery, state: FSMContext):
    _, venue_id_str, user_status = cb.data.split(':')
    venue_id = int(venue_id_str)

    access_id = ut.save_redis_temp(
        key=Key.ADD_ADMIN.value,
        data={"venue_id": venue_id, "user_status": user_status}
    )

    # Формируем ссылку
    link = f"{conf.bot_link}{Key.ADD_ADMIN.value}-{access_id}"

    await cb.message.edit_text(text=f"<b>🔗 Ссылка для подключения пользователя:</b>\n\n{link}")

    await AdminLog.add(admin_id=cb.from_user.id, action=AdminAction.LINK.value, comment=link)
