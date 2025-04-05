from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, Any
from aiogram.filters.command import CommandStart, Command
from aiogram.filters.state import StateFilter
from aiogram.filters import BaseFilter
from aiogram import Router

import asyncio

import keyboards as kb
import utils as ut
from db import User, Book
from settings import conf, log_error
from init import main_router, bot
from data import texts_dict
from handlers.admin.manage_event import manage_event_start
from enums import UserCB, MenuCommand, UserState

from google_api import add_book_gs


class MagicStartFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:

        cs = await state.get_state()
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {message.text} {cs}')
        # Проверяем, что текст присутствует и начинается с команды /start
        return bool(message.text) and message.text.startswith("/start")


# Команда старт
@main_router.message(CommandStart())
async def com_start(msg: Message, state: FSMContext):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)

    await ut.get_start_msg(user=msg.from_user)


# проверяет подписку, в случае удачи пропускает
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.BACK_START.value))
async def back_com_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await ut.get_start_msg(user=cb.from_user, msg_id=cb.message.message_id)


# Команда начать бронировать
@main_router.message(Command(MenuCommand.BOOK.command))
async def com_book(msg: Message, state: FSMContext):
    await state.clear()

    await ut.get_start_book_msg(user=msg.from_user)


# показывает кр
@main_router.callback_query(lambda cb: cb.data.startswith(UserCB.VIEW_QR.value))
async def book_comment(cb: CallbackQuery, state: FSMContext):
    _, photo_id = cb.data.split(':')

    await cb.message.answer_photo(photo=photo_id)
