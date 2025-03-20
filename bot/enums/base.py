from enum import Enum


# Команды меню
class MenuCommand(str, Enum):
    START = 'start'
    # PAY = 'pay'
    # SUB = 'sub'


# Команды меню
class UserStatus(str, Enum):
    USER = 'user'
    STAFF = 'staff'
    ADMIN = 'admin'


# Ключи к автосообщениям
class RedisKey(str, Enum):
    END_SUB = 'end_sub'


# Ключи планировщика
class SchedulerId(str, Enum):
    CHECK_SUB = 'check_sub'

