from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from datetime import datetime, timedelta

from settings import conf
from db import Venue, Event
from enums import AdminCB, Action, UserStatus, EventStep, OptionData


# Кнопки подписаться на канал
def get_admin_main_kb(user_status: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🪑 Брони', callback_data=f'{AdminCB.BOOK_START.value}')
    kb.button(text='🎫  Билеты', callback_data=f'{AdminCB.TICKET_START.value}')
    if user_status == UserStatus.ADMIN.value:
        kb.button(text='➕ Добавить ивент', callback_data=f'{AdminCB.EVENT_START.value}')
        kb.button(text='🖍 Редактировать ивент', callback_data=f'{AdminCB.EVENT_UPDATE_1.value}')
        kb.button(text='📯 Сделать рассылку', callback_data=f'{AdminCB.MAILING_START.value}')
        kb.button(text='🔗 Добавить администратора', callback_data=f'{AdminCB.ADD_START.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора заведения
def get_event_venue_kb(venues: list[Venue]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for venue in venues:
        kb.button(text=venue.name, callback_data=f'{AdminCB.EVENT_VENUE.value}:{venue.id}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# назад к имени
def get_event_back_kb(cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data=f'{cb}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора времени
def get_event_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    today = datetime.today()
    for i in range(0, 10):
        day = today + timedelta(days=i)
        day_str = day.strftime(conf.date_format)
        kb.button(text=day_str[:-5], callback_data=f'{AdminCB.EVENT_DATE.value}:{day_str}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_COVER.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_event_time_kb(popular_time: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for time_book in popular_time or []:
        kb.button(text=time_book, callback_data=f'{AdminCB.EVENT_TIME.value}:{time_book.replace(":", " ")}')

    bc_bt = InlineKeyboardBuilder()
    bc_bt.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_COVER.value}:{Action.BACK.value}')
    return kb.adjust(2).attach(bc_bt).as_markup()


# кнопки изменения мероприятия
def get_event_end_kb(event_id: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Добавить опцию', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.OPTION_NAME.value}')
    kb.button(text='🗑 Удалить опцию', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.OPTION_DEL.value}')
    kb.button(text='🖍 Изменить место проведения', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.VENUE.value}')
    kb.button(text='🖍 Изменить обложку', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.COVER.value}')
    kb.button(text='🖍 Изменить название', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.NAME.value}')
    kb.button(text='🖍 Изменить дату', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.DATE.value}')
    kb.button(text='🖍 Изменить время', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.TIME.value}')
    kb.button(
        text='✅ Обновить мероприятие' if event_id else '✅ Создать мероприятие',
        callback_data=f'{AdminCB.EVENT_END.value}'
    )
    return kb.adjust(1).as_markup()


# Кнопки выбора времени
def get_event_option_select_kb(options: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for option in options or []:
        kb.button(text=str(option), callback_data=f'{AdminCB.EVENT_OPTION.value}:{option}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_OPTION.value}:{Action.BACK.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_event_option_del_kb(options: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    i = 0
    for option in options or []:
        opt_obj = OptionData(**option)
        kb.button(text=opt_obj.name, callback_data=f'{AdminCB.EVENT_DEL_OPTION_2.value}:{i}')
        i += 1

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_OPTION.value}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора ивента для обновления
def get_update_event_kb(events: list[Event]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in events:
        kb.button(text=event.name, callback_data=f'{AdminCB.EVENT_UPDATE_2.value}:{event.id}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()
