from enum import Enum


# калбеки пользователя
class UserCB(str, Enum):
    BACK_START = 'back_start'
    VIEW_QR = 'view_qr'

    BOOK_START = 'user_book_start'
    BOOK_DATE = 'admin_book_date'
    BOOK_TIME = 'admin_book_time'
    BOOK_PEOPLE = 'admin_book_people'
    BOOK_COMMENT = 'admin_book_comment'
    BOOK_CHECK = 'admin_book_check'
    BOOK_END = 'admin_book_end'

    TICKET_START = 'user_ticket_start'
    SETTINGS_START = 'user_settings_start'
    BOOK_COUNT = 'admin_book_count'


# калбеки админа
class AdminCB(str, Enum):
    BACK_START = 'back_start'
    BOOK_START = 'admin_book_start'


