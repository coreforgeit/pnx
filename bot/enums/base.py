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


# Ключи к автосообщениям
class Action(str, Enum):
    BACK = 'back'
    ADD = 'add'
    DEL = 'del'


# Ключи к автосообщениям
class RedisKey(str, Enum):
    END_SUB = 'end_sub'


# Ключи планировщика
class SchedulerId(str, Enum):
    CHECK_SUB = 'check_sub'

