from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from settings import conf
from db import Plugin, Tariff
from enums import CB, TariffType


# Кнопки подписаться на канал
def get_subscribe_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Подписаться', url=conf.channel_link)
    kb.button(text='Я подписан', callback_data=f'{CB.CHECK_SUBSCRIBE.value}')
    return kb.adjust(1).as_markup()
