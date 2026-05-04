from enum import Enum


# калбеки пользователя
class UserCB(str, Enum):
    BACK_START = 'back_start'
    DEL_MSG = 'del_msg'

    VIEW_QR = 'view_qr'

    BOOK_START = 'user_book_start'
    BOOK_VENUE = 'user_book_venue'
    BOOK_DATE = 'user_book_date'
    BOOK_TIME = 'user_book_time'
    BOOK_PEOPLE = 'user_book_people'
    BOOK_COMMENT = 'user_book_comment'
    BOOK_CHECK = 'user_book_check'
    BOOK_END = 'user_book_end'

    TICKET_START = 'user_ticket_start'
    TICKET_EVENT = 'user_ticket_event'
    TICKET_OPTION = 'user_ticket_option'
    TICKET_PLACE = 'user_ticket_place'
    TICKET_CONFIRM = 'user_ticket_confirm'
    TICKET_END = 'user_ticket_end'
    TICKET_ALTER_PAY_1 = 'user_ticket_alter_pay_1'
    TICKET_ALTER_PAY_2 = 'user_ticket_alter_pay_2'

    SETTINGS_START = 'user_settings_start'
    SETTINGS_EDIT = 'user_settings_edit'
    SETTINGS_REMOVE_1 = 'user_settings_remove_1'
    SETTINGS_REMOVE_2 = 'user_settings_remove_2'

    BOOK_COUNT = 'user_book_count'


# калбеки админа
class AdminCB(str, Enum):
    BACK_START = 'back_start'
    SETTINGS_REMOVE_1 = 'user_settings_remove_1'
    DEL_MSG = 'del_msg'

    # BOOK_START = 'admin_book_start'
    # TICKET_START = 'admin_ticket_start'
    EVENT_UPDATE_1 = 'admin_event_update_1'
    EVENT_UPDATE_2 = 'admin_event_update_2'

    MAILING_START = 'admin_mailing_start'
    MAILING_1 = 'admin_mailing_1'
    MAILING_2 = 'admin_mailing_2'

    ADD_START = 'admin_add_start'
    ADD_VENUE = 'admin_add_venue'
    ADD_STATUS = 'admin_add_status'

    VIEW_START = 'admin_view_start'
    VIEW_TICKETS = 'admin_view_tickets'
    VIEW_BOOK = 'admin_view_book'

    SEND_MESSAGE_START = 'admin_send_message_start'

    EVENT_START = 'admin_event_start'
    EVENT_VENUE = 'admin_event_venue'
    EVENT_NAME = 'admin_event_name'
    EVENT_COVER = 'admin_event_cover'
    EVENT_CLOSE_MSG = 'admin_event_close_msg'
    EVENT_DATE = 'admin_event_date'
    EVENT_TIME = 'admin_event_time'
    EVENT_OPTION = 'admin_options'
    EVENT_DEL_OPTION_1 = 'admin_options_del_1'
    EVENT_DEL_OPTION_2 = 'admin_options_del_2'
    EVENT_BACK = 'admin_event_back'
    EVENT_EDIT = 'admin_event_edit'
    EVENT_END = 'admin_event_end'

    ALTER_PAY = 'admin_alter_pay'



