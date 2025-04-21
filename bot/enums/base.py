from enum import Enum


# Команды меню
class MenuCommand(Enum):
    START = ('start', '🔄 В начало')
    BOOK = ('book', '🪑 Бронирование столиков')
    TICKET = ('ticket', '🎫 Билеты')
    SETTINGS = ('settings', '⚙️ Мои брони')

    def __init__(self, command, label):
        self.command = command
        self.label = label


# Команды меню
class UserStatus(str, Enum):
    USER = 'user'
    STAFF = 'staff'
    ADMIN = 'admin'


# Команды меню
class BookStatus(str, Enum):
    NEW = 'new'
    CONFIRMED = 'confirmed'
    VISITED = 'visited'
    CANCELED = 'canceled'


book_status_dict = {
    BookStatus.NEW.value: 'Новая',
    BookStatus.CONFIRMED.value: 'Подтверждена',
    BookStatus.VISITED.value: 'Пришёл',
    BookStatus.CANCELED.value: 'Отменена',
}


# Ключи к автосообщениям
class Action(str, Enum):
    BACK = 'back'
    VIEW = 'view'
    ADD = 'add'
    DEL = 'del'
    SEND = 'send'


# Ключи к редису
class Key(str, Enum):
    QR_BOOK = 'book'
    QR_TICKET = 'ticket'
    ADD_ADMIN = 'add_admin'


# Ключи к редису
class NoticeKey(str, Enum):
    BOOK_DAY = 'book_day'
    BOOK_2_HOUR = 'book_2_hour'
    BOOK_NOW = 'book_now'
    BOOK_CLOSE = 'book_close'


# Ключи планировщика
class SchedulerId(str, Enum):
    CHECK_SUB = 'check_sub'

