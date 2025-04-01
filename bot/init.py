from aiogram import Dispatcher
from aiogram.types.bot_command import BotCommand
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import asyncio
import redis
import uvloop

from sqlalchemy.ext.asyncio import create_async_engine
from settings import conf
from enums import MenuCommand


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
dp = Dispatcher()
bot = Bot(
    token=conf.token,
    loop=loop,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Настройка Redis
redis_client = redis.StrictRedis(host=conf.redis_host, port=conf.redis_port, db=0)
redis_client_1 = redis.StrictRedis(host=conf.redis_host, port=conf.redis_port, db=1)


scheduler = AsyncIOScheduler(
    jobstores={
        'default': RedisJobStore(host=conf.redis_host, port=conf.redis_port, db=1)
    },
    executors={
        'default': AsyncIOExecutor()
    },
    job_defaults={
        'coalesce': True,
        'max_instances': 3
    }
)


ENGINE = create_async_engine(url=conf.db_url)


async def set_main_menu():
    await bot.set_my_commands([
        BotCommand(command=cmd.command, description=cmd.label)
        for cmd in MenuCommand
    ])
