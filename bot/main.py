import asyncio
import logging
import sys

from datetime import datetime

from handlers import dp
from init import set_main_menu, bot
from settings import conf, log_error
from db.base import init_models
# from utils.scheduler_utils import start_schedulers, shutdown_schedulers


async def main() -> None:
    await init_models()
    await set_main_menu()
    # if not conf.debug:
    #     await start_schedulers()
    # else:
    #     pass
    #     await start_schedulers()
    await dp.start_polling(bot)
    # await shutdown_schedulers()
    await bot.session.close()


if __name__ == "__main__":
    if conf.debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        log_error('start bot', wt=False)
    asyncio.run(main())
