from dataclasses import dataclass, asdict
from enum import Enum

import typing as t


class UserState(str, Enum):
    BOOK = 'book'
    EVENT = 'event'
    TICKET = 'ticket'
    MAILING = 'mailing'
    SEND_MSG = 'send_msg'
    # MAILING = 'send_admin'


@dataclass
class BaseData:
    user_id: int = None
    msg_id: int = None
    step: str = None

    def print_all(self):
        print('>>>')
        for key, value in asdict(self).items():
            print(f"{key}: {value}")

        print('---')


class BookStep(str, Enum):
    VENUE = 'venue'
    DATE = 'date'
    TIME = 'time'
    PEOPLE = 'people'
    COMMENT = 'comment'
    CHECK = 'check'
    END = 'end'


@dataclass
class BookData(BaseData):
    book_id: int = None
    book_row: int = None
    venue_id: int = None
    venue_name: str = None
    date_str: str = None
    time_str: str = None
    times_list: list[str] = None
    people_count: int = None
    comment: str = None


book_text_dict = {
    BookStep.VENUE.value: '<b>Где бы вы хотели забронировать столик?</b>',
    BookStep.DATE.value: '<b>В какой день?</b>',
    BookStep.TIME.value: '<b>В какое время?</b>\n\n'
                         '<i>Выберите из указанных вариантов или отправьте время в формате ЧЧ:ММ</i>',
    BookStep.PEOPLE.value: '<b>Сколько человек вас будет?</b>',
    BookStep.COMMENT.value: '<b>Можете оставить комментарий или пожелание (до 200 символов)</b>',
    BookStep.CHECK.value: '<b>Проверьте данные брони, если всё верно нажмите "Забронировать"</b>',
    BookStep.END.value: '<b>Бронь подтверждена</b>',
}


class EventStep(str, Enum):
    VENUE = 'venue'
    NAME = 'name'
    COVER = 'cover'
    DATE = 'date'
    TIME = 'time'
    OPTION_NAME = 'option_name'
    OPTION_PLACE = 'option_place'
    OPTION_PRICE = 'option_price'
    OPTION_DEL = 'option_del'
    END = 'end'


event_text_dict = {
    EventStep.VENUE.value: 'Выберите заведение',
    EventStep.NAME.value: 'Отправьте название мероприятия (до 50 символов)',
    EventStep.COVER.value: 'Отправьте обложку мероприятия с текстом и описанием',
    EventStep.DATE.value: 'День проведения\nВыберите из кнопок или отправьте в формате ДД:ММ:ГГГГ',
    EventStep.TIME.value: 'Время проведения\nВыберите из кнопок или отправьте в формате ЧЧ:ММ',
    EventStep.OPTION_NAME.value: 'Название опции',
    EventStep.OPTION_PLACE.value: 'Количество мест',
    EventStep.OPTION_PRICE.value: 'Стоимость',
    EventStep.END.value: 'Создать мероприятие?',
}


@dataclass
class EventData(BaseData):
    venue_id: int = None
    venue_name: str = None
    sheet_id: str = None
    name: str = None
    content_type: str = None
    text: str = None
    photo_id: str = None
    entities: str = None
    date_str: str = None
    time_str: str = None
    times_list: list[str] = None
    options: list[dict] = None
    current_option: dict = None
    top_name: list[str] = None
    top_place: list[int] = None
    top_price: list[int] = None
    event_id: int = None
    end: int = 0
    pade_id: int = 0


@dataclass
class OptionData:
    id: int = None
    name: str = None
    place: int = None
    price: int = None


# Шаги покупки
class TicketStep(str, Enum):
    EVENT = 'event'
    OPTION = 'option'
    COUNT = 'count'
    CONFIRM = 'confirm'


ticket_text_dict = {
    TicketStep.EVENT.value: 'Выберите заведение',
    TicketStep.OPTION.value: 'Выберите тип билета',
    TicketStep.COUNT.value: 'Количество билетов',
    TicketStep.CONFIRM.value: 'Ваш заказ верен?',
}


@dataclass
class TicketData(BaseData):
    event: "Event" = None
    option: "EventOption" = None
    count_place: int = None
    ticket_id_list: list = None


@dataclass
class TicketRedisData(BaseData):
    ticket_id_list: list[int] = None
    event_id: int = None
    user_id: int = None
    option_id: int = None
    full_name: str = None


@dataclass
class MailingData(BaseData):
    del_msg_id: int = None


@dataclass
class SendData(BaseData):
    for_user_id: int = None
    from_user_id: int = None
    book_text: str = None
    sender_status: str = None
    book_type: str = None
    entry_id: int = None
    base_msg_id: int = None
