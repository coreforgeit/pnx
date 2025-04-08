from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from datetime import datetime, timedelta

import math

from settings import conf
from db import Venue, Event, EventOption
from enums import UserCB, Action


# Кнопки основного меню
def get_user_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Бронь столика', callback_data=f'{UserCB.BOOK_START.value}')
    kb.button(text='Билеты', callback_data=f'{UserCB.TICKET_START.value}:{Action.VIEW.value}')
    kb.button(text='Мои брони', callback_data=f'{UserCB.SETTINGS_START.value}')
    return kb.adjust(2, 1).as_markup()


# Кнопки выбора заведения
def get_book_main_kb(venues: list[Venue]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for venue in venues:
        kb.button(text=venue.name, callback_data=f'{UserCB.BOOK_DATE.value}:{venue.id}')

    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора времени
def get_book_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    today = datetime.today()
    for i in range(0, 10):
        day = today + timedelta(days=i)
        day_str = day.strftime(conf.date_format)
        kb.button(text=day_str[:-5], callback_data=f'{UserCB.BOOK_DATE.value}:{day_str}')

    # kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_START.value}:{Action.BACK.value}')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_START.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_book_time_kb(popular_time: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for time_book in popular_time:
        kb.button(text=time_book, callback_data=f'{UserCB.BOOK_PEOPLE.value}:{time_book.replace(":", " ")}')

    bc_bt = InlineKeyboardBuilder()
    bc_bt.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_DATE.value}:{Action.BACK.value}')
    return kb.adjust(2).attach(bc_bt).as_markup()


# Кнопки выбора времени
def get_book_people_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(1, 5):
        kb.button(text=f'{i}', callback_data=f'{UserCB.BOOK_COMMENT.value}:{i}')

    kb.button(text='Нас будет больше', callback_data=f'{UserCB.BOOK_COMMENT.value}:5')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_TIME.value}:{Action.BACK.value}')
    return kb.adjust(4, 1).as_markup()


# Кнопки выбора времени
def get_book_comment_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Без комментария', callback_data=f'{UserCB.BOOK_CHECK.value}')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_PEOPLE.value}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора времени
def get_book_check_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Забронировать', callback_data=f'{UserCB.BOOK_END.value}')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_COMMENT.value}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Показать кр-код
def get_view_qr_kb(file_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Показать QR-код', callback_data=f'{UserCB.VIEW_QR.value}:{file_id}')
    return kb.adjust(1).as_markup()


# Кнопки выбора заведения
def get_ticket_event_kb(events: list[Event]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in events:
        kb.button(text=event.name, callback_data=f'{UserCB.TICKET_EVENT.value}:{event.id}')

    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора заведения
def get_ticket_options_kb(options: list[EventOption]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for option in options:
        if option.empty_place == 0:
            continue

        kb.button(
            text=f'{option.name} ({option.empty_place})',
            callback_data=f'{UserCB.TICKET_PLACE.value}:{option.id}'
        )

    kb.button(text='🔙 Назад', callback_data=f'{UserCB.TICKET_START.value}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора количества мест
def get_ticket_place_kb(empty_pace: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    row_len = 4
    for i in range(1, 9):
        if i > empty_pace:
            row_len = i / 2 if i % 2 == 0 else math.ceil(i / 2)
            break
        kb.button(text=f'{i}', callback_data=f'{UserCB.TICKET_CONFIRM.value}:{i}')

    kb_back = InlineKeyboardBuilder()
    kb_back.button(text='🔙 Назад', callback_data=f'{UserCB.TICKET_OPTION.value}')
    return kb.adjust(row_len).attach(kb_back).as_markup()


# Кнопки выбора количества мест
def get_ticket_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='✅ Подтвердить', callback_data=f'{UserCB.TICKET_END.value}')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.TICKET_PLACE.value}')
    return kb.adjust(1).as_markup()
