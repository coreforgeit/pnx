from aiogram.types import ErrorEvent, Message

from init import dp
from settings import log_error, conf


# if not conf.debug:
@dp.errors()
async def error_handler(ex: ErrorEvent):
    tb, msg = log_error (ex)
    user_id = ex.update.message.from_user.id if ex.update.message else None
