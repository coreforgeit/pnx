import asyncio
import logging
import sys

from aiogram import Dispatcher
from datetime import datetime

import db
from init import set_main_menu, bot
from settings import conf, log_error
from db.base import init_models
from utils.scheduler_ut import start_schedulers, shutdown_schedulers
from handlers import main_router
from handlers.admin.manage_event import admin_router
from handlers.user import user_router
from handlers.exceptions import error_router


dp = Dispatcher()


async def main() -> None:
    # await get_pay_token()
    await init_models()
    await set_main_menu()
    await db.close_old()
    if not conf.debug:
        await start_schedulers()
    else:
        pass
        # await start_schedulers()

    dp.include_router(main_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(error_router)
    await dp.start_polling(bot)
    await shutdown_schedulers()
    await bot.session.close()


if __name__ == "__main__":
    if conf.debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        log_error('start bot', wt=False)
    asyncio.run(main())
