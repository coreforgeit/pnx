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

book_status_choice = tuple(book_status_dict.items())


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


# Ключи к автосообщениям
class AdminAction(str, Enum):
    ADMIN_SEND = 'admin_send'
    USER_SEND = 'user_send'
    MAILING = 'mailing'
    LINK = 'link'
    BOOK = 'book'
    TICKET = 'ticket'
    ADD = 'add'
    DEL = 'del'
    EDIT = 'edit'


admin_action_choice = (
    (AdminAction.ADMIN_SEND.value, 'Написал пользователю'),
    (AdminAction.USER_SEND.value, 'Получил сообщение'),
    (AdminAction.MAILING.value, 'Сделал рассылку'),
    (AdminAction.ADD.value, 'Добавил'),
    (AdminAction.DEL.value, 'Удалил'),
    (AdminAction.EDIT.value, 'Изменил'),
)
