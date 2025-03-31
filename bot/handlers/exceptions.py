from aiogram.types import ErrorEvent, Message, CallbackQuery

from init import dp
from settings import log_error, conf


# if not conf.debug:
@dp.errors()
async def error_handler(ex: ErrorEvent):
    tb, msg = log_error (ex)
    user_id = ex.update.message.from_user.id if ex.update.message else None



@dp.callback_query()
async def in_dev(cb: CallbackQuery):
    log_error(f'>>> {cb.data}', wt=False)
    await cb.answer(f'🛠 Функция в разработке', show_alert=True)