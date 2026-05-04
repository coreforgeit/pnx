from aiogram import BaseMiddleware

from settings import begin_connection


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with begin_connection() as session:
            data['session'] = session
            return await handler(event, data)
