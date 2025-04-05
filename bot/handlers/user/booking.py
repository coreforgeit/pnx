from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from dataclasses import asdict
from datetime import datetime

import asyncio

import db
import keyboards as kb
import utils as ut
from google_api import add_book_gs
from db import User, Book, Venue
from settings import conf, log_error
from init import user_router, bot
from data import texts_dict
from enums import UserCB, BookData, UserState, BookStep, book_text_dict, Action, Key


# старт брони столиков
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_START.value))
async def book_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await ut.get_start_book_msg(user=cb.from_user, msg_id=cb.message.message_id)


async def get_main_book_msg(state: FSMContext, markup: InlineKeyboardMarkup = None):
    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.print_all()

    people_count = data_obj.people_count
    if data_obj.people_count and data_obj.people_count >= 5:
        people_count = 'компания'

    row_list = [
        f'<b>{data_obj.venue_name}</b>\n\n',
        f'Дата: {data_obj.date_str}\n',
        f'Время: {data_obj.time_str}\n',
        f'Количество персон: {people_count}\n',
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


# проверяем наличие столиков
async def check_available_tables(chat_id: int, data_obj: BookData):
    available_tables_count = await db.get_available_tables(
        venue_id=data_obj.venue_id,
        book_date=datetime.strptime(data_obj.date_str, conf.date_format).date(),
        book_time=datetime.strptime(data_obj.time_str, conf.time_format).time(),
    )

    if available_tables_count == 0:
        text = f'❗️К сожалению, все столики на это время забронированы'
        await ut.send_text_alert(chat_id=chat_id, text=text)
        return True

    else:
        return False


# записывет заведение, запрашивает время
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_DATE.value))
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
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_TIME.value))
async def book_time(cb: CallbackQuery, state: FSMContext):
    _, date_str = cb.data.split(':')

    data = await state.get_data()
    data_obj = BookData(**data)

    if date_str != Action.BACK.value:
        exist_book = await Book.get_booking(
            venue_id=data_obj.venue_id, user_id=cb.from_user.id, date_book=datetime.strptime(date_str, conf.date_format).date()
        )

        # print(f'>>>>>>>>>> {type(exist_book)}')
        # print(exist_book)

        if exist_book and not conf.debug:
            text = (
                f'❗️ Вы можете создать только одну бронь\n\n'
                f'У вас уже забронирован столик на {exist_book.date_book_str()} в '
                f'{exist_book.time_book_str()}'
            )
            await ut.send_text_alert(chat_id=cb.from_user.id, text=text)
            return

        data_obj.date_str = date_str

        data_obj.times_list = await Book.get_top_times()

    data_obj.step = BookStep.TIME.value
    await state.update_data(data=asdict(data_obj))

    await get_main_book_msg(state, markup=kb.get_book_time_kb(data_obj.times_list))


# записывает время, запрашивает количество мест
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_PEOPLE.value))
async def book_people(cb: CallbackQuery, state: FSMContext):
    _, time_str = cb.data.split(':')

    time_str = time_str.replace(' ', ':')
    data = await state.get_data()
    data_obj = BookData(**data)

    if time_str != Action.BACK.value:
        data_obj.time_str = time_str

        is_full = await check_available_tables(chat_id=cb.from_user.id, data_obj=data_obj)
        if is_full:
            return

    data_obj.step = BookStep.PEOPLE.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=kb.get_book_people_kb())


# записывает количество мест, запрашивает коммент
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_COMMENT.value))
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
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_CHECK.value))
async def book_skip_comment(cb: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    data_obj = BookData(**data)

    data_obj.step = BookStep.CHECK.value

    await state.update_data(data=asdict(data_obj))
    await get_main_book_msg(state, markup=kb.get_book_check_kb())


# принимает комментарий
@user_router.message(StateFilter(UserState.BOOK.value))
async def book_comment(msg: Message, state: FSMContext):
    await msg.delete()

    data = await state.get_data()
    data_obj = BookData(**data)

    if data_obj.step == BookStep.TIME.value:
        book_time = ut.hand_time_format(msg.text)
        if book_time:
            data_obj.time_str = book_time

            is_full = await check_available_tables(chat_id=msg.from_user.id, data_obj=data_obj)
            if is_full:
                return

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


# заканчиваем бронирование
@user_router.callback_query(lambda cb: cb.data.startswith(UserCB.BOOK_END.value))
async def book_end(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data_obj = BookData(**data)
    await state.clear()

    is_full = await check_available_tables(chat_id=cb.from_user.id, data_obj=data_obj)
    if is_full:
        return

    # сохраняем бронь
    date_book = datetime.strptime(data_obj.date_str, conf.date_format).date()
    time_book = datetime.strptime(data_obj.time_str, conf.time_format).time()
    book_id = await Book.add(
        user_id=cb.from_user.id,
        venue_id=data_obj.venue_id,
        date_book=date_book,
        time_book=time_book,
        comment=data_obj.comment,
        people_count=data_obj.people_count
    )

    #     создаём и отправляем кр-код
    text = f'Ждём вас {data_obj.date_str} в {data_obj.time_str} в {data_obj.venue_name}'
    qr_id = await ut.generate_and_sand_qr(
        chat_id=cb.from_user.id,
        qr_data=f'{Key.QR_BOOK.value}:{cb.from_user.id}:{book_id}',
        caption=text
    )

    # создаём уведомления
    ut.create_book_notice(book_id=book_id, book_date=date_book, book_time=time_book)
    # пишем админу
    comment = f'\n\n<i>{data_obj.comment}</i>' if data_obj.comment else ''
    text = (f'<b>Новая бронь!</b>\n\n'
            f'{data_obj.date_str} {data_obj.time_str} на {data_obj.people_count} чел. {cb.from_user.full_name}'
            f'{comment}')
    await bot.send_message(chat_id=conf.admin_chat, text=text)

#     отправляем в таблицу
    venue = await Venue.get_by_id(data_obj.venue_id)
    last_day_book = await Book.get_last_book_day(date_book=date_book)
    gs_row = await add_book_gs(
        spreadsheet_id=venue.book_gs_id,
        sheet_name=data_obj.date_str,
        booking_time=data_obj.time_str,
        full_name=cb.from_user.full_name,
        count_place=data_obj.people_count,
        comment=data_obj.comment,
        attended=False,
        start_row=last_day_book.gs_row + 1 if last_day_book else 2
    )

    await Book.update(book_id, qr_id=qr_id, gs_row=gs_row)




