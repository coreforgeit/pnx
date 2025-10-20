from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from datetime import datetime, timedelta

from settings import conf
from db import Venue, Event, TicketStatRow, BookStatRow
from enums import AdminCB, Action, UserStatus, EventStep, OptionData, Key


# Кнопки подписаться на канал
def get_admin_main_kb(user_status: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🪑 Брони', callback_data=f'{AdminCB.VIEW_START.value}:{Key.QR_BOOK.value}')
    kb.button(text='🎫  Билеты', callback_data=f'{AdminCB.VIEW_START.value}:{Key.QR_TICKET.value}')
    if user_status == UserStatus.ADMIN.value:
        kb.button(text='➕ Добавить ивент', callback_data=f'{AdminCB.EVENT_START.value}')
        kb.button(text='🖍 Редактировать ивент', callback_data=f'{AdminCB.EVENT_UPDATE_1.value}')
        kb.button(text='📯 Сделать рассылку', callback_data=f'{AdminCB.MAILING_START.value}')
        kb.button(text='🔗 Добавить администратора', callback_data=f'{AdminCB.ADD_START.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора заведения
def get_event_venue_kb(venues: list[Venue], cb: str = AdminCB.EVENT_VENUE.value) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for venue in venues:
        kb.button(text=venue.name, callback_data=f'{cb}:{venue.id}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# удаляет сообщение
def get_cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='❌ Отмена', callback_data=f'{AdminCB.DEL_MSG.value}')
    return kb.adjust(1).as_markup()


# назад к имени
def get_event_back_kb(cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data=f'{cb}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# пропустить последнее сообщение
def get_skip_close_msg_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Пропустить', callback_data=f'{AdminCB.EVENT_CLOSE_MSG.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора времени
def get_event_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    today = datetime.today()
    for i in range(0, 10):
        day = today + timedelta(days=i)
        day_str = day.strftime(conf.date_format)
        kb.button(text=day_str[:-5], callback_data=f'{AdminCB.EVENT_DATE.value}:{day_str}')

    # kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_VENUE.value}:{Action.BACK.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_event_time_kb(popular_time: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for time_book in popular_time or []:
        kb.button(text=time_book, callback_data=f'{AdminCB.EVENT_TIME.value}:{time_book.replace(":", " ")}')

    bc_bt = InlineKeyboardBuilder()
    # bc_bt.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_COVER.value}:{Action.BACK.value}')
    return kb.adjust(2).attach(bc_bt).as_markup()


# кнопки изменения мероприятия
def get_event_end_kb(event_id: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Добавить опцию', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.OPTION_NAME.value}')
    kb.button(text='🗑 Удалить опцию', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.OPTION_DEL.value}')
    kb.button(text='🖍 Изменить место проведения', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.VENUE.value}')
    kb.button(text='🖍 Изменить обложку', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.COVER.value}')
    kb.button(text='🖍 Изменить закрываеющее сообщение', callback_data=f'{AdminCB.EVENT_EDIT.value}:{EventStep.CLOSE_MSG.value}')
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

    # kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_OPTION.value}:{Action.BACK.value}')
    return kb.adjust(2).as_markup()


# Кнопки выбора времени
def get_event_option_del_kb(options: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    i = 0
    for option in options or []:
        opt_obj = OptionData(**option)
        kb.button(text=opt_obj.name, callback_data=f'{AdminCB.EVENT_DEL_OPTION_2.value}:{i}')
        i += 1

    # kb.button(text='🔙 Назад', callback_data=f'{AdminCB.EVENT_OPTION.value}:{Action.BACK.value}')
    return kb.adjust(1).as_markup()


# Кнопки выбора ивента для обновления
def get_update_event_kb(events: list[Event]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in events:
        kb.button(text=event.name, callback_data=f'{AdminCB.EVENT_UPDATE_2.value}:{event.id}')

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# список ивентов
def get_ticket_state_kb(ticket_stat: list[TicketStatRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in ticket_stat:
        kb.button(
            text=f'({event.ticket_count}) {event.event_name}',
            callback_data=f'{AdminCB.VIEW_BOOK.value}:{Key.QR_TICKET.value}:{event.event_id}'
        )

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# список броней
def get_book_state_kb(book_stat: list[BookStatRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book_date in book_stat:
        date_str = book_date.date.strftime(conf.date_format)
        kb.button(
            text=f'{date_str[:-5]} ({book_date.book_count})',
            callback_data=f'{AdminCB.VIEW_BOOK.value}:{Key.QR_BOOK.value}:{date_str}'
        )

    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.BACK_START.value}')
    return kb.adjust(1).as_markup()


# изменение для каждой брони
def get_book_manage_kb(book_id: int, book_type: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text='📲 Написать пользователю', callback_data=f'{AdminCB.SEND_MESSAGE_START.value}:{book_type}:{book_id}:0'
    )
    kb.button(text='🗑 Отменить бронь', callback_data=f'{AdminCB.SETTINGS_REMOVE_1.value}:{book_type}:{book_id}')

    return kb.adjust(1).as_markup()


# изменение для каждой брони
def get_mailing_send_kb(second: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if second:
        kb.button(text='📲 Подтвердить отправку', callback_data=f'{AdminCB.MAILING_2.value}:{Action.SEND.value}')
    else:
        kb.button(text='📲 Отправить сообщение', callback_data=f'{AdminCB.MAILING_1.value}')

    kb.button(text='🗑 Удалить', callback_data=f'{AdminCB.MAILING_2.value}:{Action.DEL.value}')
    return kb.adjust(1).as_markup()


# ответить админу
def get_send_answer_kb(user_id: int, book_id: int, book_type: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='📲 Ответить', callback_data=f'{AdminCB.SEND_MESSAGE_START.value}:{book_type}:{book_id}:{user_id}')
    return kb.adjust(1).as_markup()


# ответить админу
def get_add_admin_status_kb(venue_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Админ', callback_data=f'{AdminCB.ADD_STATUS.value}:{venue_id}:{UserStatus.ADMIN.value}')
    kb.button(text='Персонал', callback_data=f'{AdminCB.ADD_STATUS.value}:{venue_id}:{UserStatus.STAFF.value}')
    kb.button(text='🔙 Назад', callback_data=f'{AdminCB.ADD_START.value}')
    return kb.adjust(2, 1).as_markup()


# выбор способа оплаты
def get_ticket_pay_confirm_kb(ticket_id: int, redis_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text='📲 Написать пользователю',
        callback_data=f'{AdminCB.SEND_MESSAGE_START.value}:{Key.QR_TICKET.value}:{ticket_id}:0'
    )
    kb.button(text='✅ Подтвердить оплату', callback_data=f'{AdminCB.ALTER_PAY.value}:{Action.CONF.value}:{redis_key}')
    kb.button(text='❌ Удалить билеты', callback_data=f'{AdminCB.ALTER_PAY.value}:{Action.DEL.value}:{redis_key}')
    return kb.adjust(1).as_markup()


# отменяет бронь в группе
def get_confirm_group_book(book_type: str, book_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🗑 Отменить бронь', callback_data=f'{AdminCB.SETTINGS_REMOVE_1.value}:{book_type}:{book_id}')
    return kb.adjust(1).as_markup()
