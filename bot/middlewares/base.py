from aiogram import BaseMiddleware

from settings import async_session_factory


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session_factory() as session:
            data['session'] = session
            return await handler(event, data)
