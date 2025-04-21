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
from db import User, Ticket, Book, EventOption, Event, Venue
from settings import conf, log_error
from init import bot, admin_router, redis_client
from enums import AdminCB, UserState, Action, Key, SendData, UserStatus, MailingData


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

    # Формируем payload
    payload = {
        "venue_id": venue_id,
        "user_status": user_status
    }

    # Генерация уникального кода
    access_id = uuid4().hex

    # Сохраняем в Redis на 1 сутки
    await redis_client.setex(f"{Key.ADD_ADMIN.value}:{access_id}", 86400, str(payload))

    # Формируем ссылку
    link = f"https://t.me/{conf.bot_username}?start=add_{access_id}"

    await cb.message.edit_text(
        f"✅ Ссылка для подключения пользователя:\n\n<a href='{link}'>{link}</a>",
    )



# from uuid import uuid4
# from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from redis.asyncio import Redis
#
# redis = Redis.from_url(conf.redis_url, decode_responses=True)


# @admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_START.value))
# async def add_start(cb: CallbackQuery, state: FSMContext):
#     await state.clear()
#     venues = await Venue.get_all()
#
#     kb_markup = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text=venue.name, callback_data=f"{AdminCB.ADD_VENUE.value}:{venue.id}")]
#             for venue in venues
#         ]
#     )
#
#     await cb.message.edit_text("<b>Выберите заведение:</b>", reply_markup=kb.)
#
#
# @admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_VENUE.value))
# async def add_venue(cb: CallbackQuery, state: FSMContext):
#     _, venue_id_str = cb.data.split(':')
#     venue_id = int(venue_id_str)
#
#     data = SendData(venue_id=venue_id)
#     await state.update_data(data=asdict(data))
#
#     kb_markup = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(text="Стаф", callback_data=f"{AdminCB.ADD_STATUS.value}:{venue_id}:{UserStatus.STAFF.value}"),
#                 InlineKeyboardButton(text="Админ", callback_data=f"{AdminCB.ADD_STATUS.value}:{venue_id}:{UserStatus.ADMIN.value}")
#             ]
#         ]
#     )
#
#     await cb.message.edit_text("<b>Выберите уровень доступа:</b>", reply_markup=kb_markup)
#
#
# @admin_router.callback_query(lambda cb: cb.data.startswith(AdminCB.ADD_STATUS.value))
# async def add_status(cb: CallbackQuery, state: FSMContext):
#     _, venue_id_str, user_status = cb.data.split(':')
#     venue_id = int(venue_id_str)
#
#     # Формируем payload
#     payload = {
#         "venue_id": venue_id,
#         "user_status": user_status
#     }
#
#     # Генерация уникального кода
#     access_id = uuid4().hex
#
#     # Сохраняем в Redis на 1 сутки
#     await redis.setex(f"user:add:{access_id}", 86400, str(payload))
#
#     # Формируем ссылку
#     link = f"https://t.me/{conf.bot_username}?start=add_{access_id}"
#
#     await cb.message.edit_text(
#         f"✅ Ссылка для подключения пользователя:\n\n<a href='{link}'>{link}</a>",
#         parse_mode="HTML"
#     )
