from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from settings import conf
from enums import UserCB


# Кнопки подписаться на канал
def get_user_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Бронь столика', callback_data=f'{UserCB.BOOK_START.value}')
    kb.button(text='Билеты', callback_data=f'{UserCB.TICKET_START.value}')
    kb.button(text='Мои брони', callback_data=f'{UserCB.SETTINGS_START.value}')
    return kb.adjust(2, 1).as_markup()
