from dataclasses import dataclass, asdict
from enum import Enum


class UserState(str, Enum):
    BOOK = 'book'


class BookStep(str, Enum):
    VENUE = 'venue'
    DATE = 'date'
    TIME = 'time'
    PEOPLE = 'people'
    TABLE = 'table'
    CHECK = 'check'
    END = 'end'


@dataclass
class BaseData:
    user_id: int = None
    msg_id: int = None
    step: str = None


@dataclass
class BookData(BaseData):
    venue_id: int = None
    venue_name: str = None
    date_str: str = None
    time_str: str = None
    times_list: list[str] = None
    people_count: int = None
    table_id: int = None
    name_id: int = None


book_text_dict = {
    BookStep.VENUE.value: '<b>Где бы вы хотели забронировать столик?</b>',
    BookStep.DATE.value: '<b>В какой день?</b>',
    BookStep.TIME.value: '<b>В какое время?</b>',
    BookStep.PEOPLE.value: '<b>Сколько человек вас будет?</b>',
    BookStep.TABLE.value: '<b>Выберите столик</b>',
    BookStep.CHECK.value: '<b>Если всё верно, нажмите "Подтвердить"</b>',
    BookStep.END.value: '<b><Бронь подтверждена</b>',
}
