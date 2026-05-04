import typing as t
import sqlalchemy as sa

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession

METADATA = sa.MetaData ()


# async def init_models():
#     async with ENGINE.begin () as conn:
#         await conn.run_sync (METADATA.create_all)


class Base(DeclarativeBase):
    metadata = METADATA

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"

    @classmethod
    async def get_all(cls, session: AsyncSession) -> t.Optional[list[t.Self]]:
        """Возвращает все активные строки"""

        query = sa.select(cls).where(cls.is_active == True)

        result = await session.execute(query)

        return result.scalars().all()
        # return result.all()

    @classmethod
    async def get_by_id(cls, entry_id: int, session: AsyncSession) -> t.Optional[t.Self]:
        """Возвращает строку по id"""

        query = sa.select(cls).where(cls.id == entry_id)

        result = await session.execute(query)

        return result.scalars().first()
