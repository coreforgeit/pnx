from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t
import random

from .base import Base, begin_connection
from enums import UserStatus


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    name: Mapped[str] = mapped_column(sa.String)
    time_open: Mapped[time] = mapped_column(sa.Time)
    time_close: Mapped[time] = mapped_column(sa.Time, server_default='23:59')
    table_count: Mapped[int] = mapped_column(sa.Integer)
    book_len: Mapped[int] = mapped_column(sa.Integer, server_default='180')
    book_gs_id: Mapped[str] = mapped_column(sa.String, nullable=True)
    event_gs_id: Mapped[str] = mapped_column(sa.String, nullable=True)
    admin_chat_id: Mapped[int] = mapped_column(sa.BigInteger, default=random.randint(10000, 99999))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=True)

    @classmethod
    async def get_by_admin_chat(cls, chat_id: int) -> t.Optional[t.Self]:
        query = sa.select(cls).where(cls.admin_chat_id == chat_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().first()

    @classmethod
    async def update(cls, venue_id: int, chat_id: int) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == venue_id).values(updated_at=now)

        if chat_id:
            query = query.values(admin_chat_id=chat_id)

        async with begin_connection() as conn:
            await conn.execute(query)
            await conn.commit()

