from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command

import asyncio

import keyboards as kb
import utils as ut
from db import User
from settings import conf, log_error
from init import dp, bot
from data import texts_dict
from enums import UserCB, MenuCommand


# Команда старт
@dp.message(Command(MenuCommand.SETTINGS.command))
async def com_start(msg: Message, state: FSMContext):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)

    await ut.get_start_msg(user=msg.from_user)


# проверяет подписку, в случае удачи пропускает
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BACK_START.value))
async def back_com_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()