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
    return kb.adjust(2, 1).as_markup()


# Кнопки выбора времени
def get_book_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    today = datetime.today()
    for i in range(0, 10):
        day_str = today.strftime(conf.date_format)
        kb.button(text=day_str, callback_data=f'{UserCB.BOOK_TIME.value}:{day_str}')

    kb.button(text='🔙 Назад', callback_data=f'{UserCB.BOOK_DATE.value}:{Action.BACK.value}')
    return kb.adjust(2, 1).as_markup()
