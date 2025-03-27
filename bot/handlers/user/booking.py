from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from db import User, Book, Venue
from settings import conf, log_error
from init import dp, bot
from data import texts_dict
from enums import UserCB, BookData, UserState, BookStep, book_text_dict


# старт брони столиков
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_START.value))
async def book_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await ut.get_start_book_msg(user=cb.from_user, msg_id=cb.message.message_id)


async def get_main_book_msg(state: FSMContext, markup: InlineKeyboardMarkup):
    data = await state.get_data()
    data_obj = BookData(**data)

    row_list = [
        f'{data_obj.venue_name}\n',
        f'Дата: {data_obj.date_str}\n',
        f'Время: {data_obj.date_str}\n',
        f'Столик: {data_obj.date_str}\n',
    ]
    text = ''.join(row for row in row_list if 'None' not in row)
    text += f'\n\n{book_text_dict.get(data_obj.step)}'

    await bot.edit_message_text(
        chat_id=data_obj.user_id,
        message_id=data_obj.msg_id,
        text=text,
        reply_markup=markup
    )


# записывет заведение, запрашивает время
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_TIME.value))
async def book_time(cb: CallbackQuery, state: FSMContext):
    _, venue_id_str = cb.data.split(':')
    venue_id = int(venue_id_str)

    current_state = await state.get_state()
    if not current_state:
        await state.set_state(UserState.BOOK.value)
        data_obj = BookData()

        venue = await Venue.get_by_id(venue_id)
        #
        # time_list = await Book.get_top_times()
        # time_list = map(str, time_list)

        # data_obj.times_list = time_list
        data_obj.user_id = cb.from_user.id
        data_obj.msg_id = cb.message.message_id
        data_obj.step = BookStep.DATE.value

        data_obj.venue_id = venue_id
        data_obj.venue_name = venue.name

        await state.update_data(data=asdict(data_obj))

    # else:
    #     data = await state.get_data()
    #     data_obj = BookData(**data)

    await get_main_book_msg(state, markup=kb.get_book_date_kb())



