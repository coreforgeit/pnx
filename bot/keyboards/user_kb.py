from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from datetime import datetime, timedelta

from settings import conf
from db import Venue
from enums import UserCB, Action


# Кнопки основного меню
def get_user_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Бронь столика', callback_data=f'{UserCB.BOOK_START.value}')
    kb.button(text='Билеты', callback_data=f'{UserCB.TICKET_START.value}')
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
        kb.button(text=day_str[:-5], callback_data=f'{UserCB.BOOK_TIME.value}:{day_str}')

    # kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_START.value}:{Action.BACK.value}')
    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_START.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_book_time_kb(popular_time: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for time_book in popular_time:
        kb.button(text=time_book, callback_data=f'{UserCB.BOOK_PEOPLE.value}:{time_book}')

    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_DATE.value}:{Action.BACK.value}')
    return kb.adjust(2).as_markup()


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
