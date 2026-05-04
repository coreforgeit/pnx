import typing as t

from sqlalchemy.ext.asyncio import AsyncSession

from settings import async_session_factory


async def get_session() -> t.AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
