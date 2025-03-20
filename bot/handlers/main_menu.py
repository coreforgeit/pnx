from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandStart

import asyncio

import keyboards as kb
import utils as ut
from db import User
from settings import conf, log_error
from init import dp, bot
from data import texts_dict
from enums import CB


# Команда старт
@dp.message(CommandStart())
async def com_start(msg: Message, state: FSMContext):
    await state.clear()

    # добавляем или обновляем данные пользователя
    await User.add(user_id=msg.from_user.id, full_name=msg.from_user.full_name, username=msg.from_user.username)

    # проверяем подписку
    is_sub = await ut.check_subscribe(msg.from_user.id)

    if is_sub:
        await ut.sent_main_msg(msg.from_user.id)

    else:
        await ut.send_subscribe_msg(msg.from_user.id)


# проверяет подписку, в случае удачи пропускает
@dp.callback_query(lambda cb: cb.data.startswith(CB.CHECK_SUBSCRIBE.value))
async def check_subscribe(cb: CallbackQuery, state: FSMContext):
    # проверяем подписку
    is_sub = await ut.check_subscribe(cb.from_user.id)

    if is_sub:
        # удаляем сообщение
        await cb.message.answer('Видим вашу подписку, сейчас отправим инструкцию...')
        # ждём 5 секунд
        await asyncio.sleep(5)

        await ut.sent_main_msg(cb.from_user.id)

    else:
        await cb.answer(texts_dict.get('check_subscribe'), show_alert=True)
