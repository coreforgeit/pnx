from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from dataclasses import asdict

import asyncio

import keyboards as kb
import utils as ut
from db import User, Book, Venue
from settings import conf, log_error
from init import dp, bot
from data import texts_dict
from enums import UserCB, BookData, UserState, BookStep, book_text_dict, Action


# старт брони столиков
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_START.value))
async def book_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await ut.get_start_book_msg(user=cb.from_user, msg_id=cb.message.message_id)


async def get_main_book_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.print_all()

    row_list = [
        f'<b>{data_obj.venue_name}</b>\n\n',
        f'Дата: {data_obj.date_str}\n',
        f'Время: {data_obj.time_str}\n',
        f'Количество персон: {data_obj.people_count}\n',
        f'Комментарий: {data_obj.comment}\n',
    ]
    text = ''.join(row for row in row_list if 'None' not in row).strip()

    text += f'\n\n{book_text_dict.get(data_obj.step)}'

    await bot.edit_message_text(
        chat_id=data_obj.user_id,
        message_id=data_obj.msg_id,
        text=text,
        reply_markup=markup
    )


# записывет заведение, запрашивает время
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_DATE.value))
async def book_date(cb: CallbackQuery, state: FSMContext):
    _, venue_id_str = cb.data.split(':')

    current_state = await state.get_state()
    if not current_state:
        venue_id = int(venue_id_str)

        await state.set_state(UserState.BOOK.value)
        data_obj = BookData()

        venue = await Venue.get_by_id(venue_id)

        data_obj.user_id = cb.from_user.id
        data_obj.msg_id = cb.message.message_id
        data_obj.step = BookStep.DATE.value

        data_obj.venue_id = venue_id
        data_obj.venue_name = venue.name

        await state.update_data(data=asdict(data_obj))

    await get_main_book_msg(state, markup=kb.get_book_date_kb())


# записывает дату, запрашивает время
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_TIME.value))
async def book_time(cb: CallbackQuery, state: FSMContext):
    _, date_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = BookData(**data)

    if date_str != Action.BACK.value:
        data_obj.date_str = date_str

        data_obj.times_list = await Book.get_top_times()

    data_obj.step = BookStep.TIME.value
    await state.update_data(data=asdict(data_obj))

    await get_main_book_msg(state, markup=kb.get_book_time_kb(data_obj.times_list))


# записывает время, запрашивает количество мест
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_PEOPLE.value))
async def book_people(cb: CallbackQuery, state: FSMContext):
    _, time_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = BookData(**data)

    if time_str != Action.BACK.value:
        data_obj.time_str = time_str

    data_obj.step = BookStep.PEOPLE.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=kb.get_book_people_kb())


# записывает количество мест, запрашивает коммент
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_COMMENT.value))
async def book_comment(cb: CallbackQuery, state: FSMContext):
    _, people_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = BookData(**data)

    if people_str != Action.BACK.value:
        data_obj.people_count = int(people_str)

    data_obj.step = BookStep.COMMENT.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=kb.get_book_comment_kb())


# пропустить коммент
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_CHECK.value))
async def book_skip_comment(cb: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.step = BookStep.CHECK.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=kb.get_book_check_kb())


# принимает комментарий
@dp.message(StateFilter(UserState.BOOK.value))
async def book_comment(msg: Message, state: FSMContext):
    await msg.delete()

    data = await state.get_data()
    data_obj = BookData(**data)

    if data_obj.step == BookStep.TIME.value:
        book_time = ut.hand_time_format(msg.text)
        if book_time:
            data_obj.time_str = book_time
            data_obj.step = BookStep.PEOPLE.value

            markup = kb.get_book_people_kb()

        else:
            await ut.send_text_alert(chat_id=msg.from_user.id, text='❗️ Неверный формат времени')
            return

    elif data_obj.step == BookStep.COMMENT.value:

        data_obj.comment = msg.text[:255]
        data_obj.step = BookStep.CHECK.value

        markup = kb.get_book_check_kb()

    else:
        await ut.send_text_alert(chat_id=msg.from_user.id, text='❗️ Выберите из предложенных вариантов')
        return

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=markup)


# пропустить коммент
@dp.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_END.value))
async def book_end(cb: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.step = BookStep.END.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state)
