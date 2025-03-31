from dataclasses import dataclass, asdict
from enum import Enum


class UserState(str, Enum):
    BOOK = 'book'


class BookStep(str, Enum):
    VENUE = 'venue'
    DATE = 'date'
    TIME = 'time'
    PEOPLE = 'people'
    COMMENT = 'comment'
    CHECK = 'check'
    END = 'end'


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


@dataclass
class BookData(BaseData):
    venue_id: int = None
    venue_name: str = None
    date_str: str = None
    time_str: str = None
    times_list: list[str] = None
    people_count: int = None
    comment: str = None
    name_id: int = None


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
