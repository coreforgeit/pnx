from aiogram.types import ErrorEvent, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from init import error_router
from db import LogsError
from settings import log_error, conf


# if not conf.debug:
@error_router.errors()
async def error_handler(ex: ErrorEvent, session: AsyncSession):
    tb, msg = log_error (ex)
    user_id = ex.update.message.from_user.id if ex.update.message else None

    await LogsError.add(user_id=user_id, traceback=tb, message=msg, session=session)


@error_router.callback_query()
async def in_dev(cb: CallbackQuery):
    log_error(f'>>> {cb.data}', wt=False)
    await cb.answer(f'🛠 Функция в разработке', show_alert=True)


# принимает комментарий
@error_router.message()
async def lost_msg(msg: Message):
    print(msg.chat.id)
    print(msg.chat.full_name)
