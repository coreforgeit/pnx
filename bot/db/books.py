from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from enums import UserStatus


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    user_id: Mapped[int] = mapped_column(sa.BigInteger)
    time_book: Mapped[time] = mapped_column(sa.Time())
    date_book: Mapped[date] = mapped_column(sa.Date())
    table_id: Mapped[int] = mapped_column(sa.Integer())
    is_come: Mapped[bool] = mapped_column(sa.Boolean(), default=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), default=True)

    @classmethod
    async def get_top_times(cls, limit: int = 8) -> list[time]:
        query = (
            sa.select(cls.time_book, sa.func.count(cls.time_book).label("count"))
            .group_by(cls.time_book)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            popular_times = [row.time_book for row in result.all()]

        return popular_times

