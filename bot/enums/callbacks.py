from enum import Enum


# калбеки
class UserCB(str, Enum):
    CHECK_SUBSCRIBE = 'check_subscribe'
    SELECT_PLUGIN = 'select_plugin'
    CREATE_PAY_URL = 'create_pay_url'


# калбеки
class AdminCB(str, Enum):
    CHECK_SUBSCRIBE = 'check_subscribe'
    SELECT_PLUGIN = 'select_plugin'
    CREATE_PAY_URL = 'create_pay_url'
