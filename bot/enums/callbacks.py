from enum import Enum


# калбеки пользователя
class UserCB(str, Enum):
    BACK_START = 'back_start'
    BOOK_START = 'user_book_start'
    TICKET_START = 'user_ticket_start'
    SETTINGS_START = 'user_settings_start'
    BOOK_DATE = 'admin_book_time'
    BOOK_TIME = 'admin_book_time'
    BOOK_COUNT = 'admin_book_count'


# калбеки админа
class AdminCB(str, Enum):
    BACK_START = 'back_start'
    BOOK_START = 'admin_book_start'


