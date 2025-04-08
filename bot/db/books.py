from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from settings import conf
from enums import UserStatus


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    user_id: Mapped[int] = mapped_column(sa.BigInteger)
    venue_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("venues.id"))
    time_book: Mapped[time] = mapped_column(sa.Time())
    date_book: Mapped[date] = mapped_column(sa.Date())
    people_count: Mapped[int] = mapped_column(sa.Integer())
    comment: Mapped[str] = mapped_column(sa.String())
    qr_id: Mapped[str] = mapped_column(sa.String(), nullable=True)
    gs_row: Mapped[int] = mapped_column(sa.Integer(), default=2)
    status: Mapped[str] = mapped_column(sa.String())

    # is_come: Mapped[bool] = mapped_column(sa.Boolean(), default=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), default=True)

    venue: Mapped["Venue"] = relationship("Venue", backref="bookings")

    def time_book_str(self) -> str:
        return self.time_book.strftime(conf.time_format)

    def date_book_str(self) -> str:
        return self.date_book.strftime(conf.date_format)

    @classmethod
    async def add(
            cls,
            user_id: int,
            venue_id: int,
            time_book: time,
            date_book: date,
            comment: str,
            status: str,
            people_count: int
    ) -> int:
        now = datetime.now()
        query = sa.insert(cls).values(
            created_at=now,
            updated_at=now,
            user_id=user_id,
            venue_id=venue_id,
            time_book=time_book,
            date_book=date_book,
            comment=comment,
            status=status,
            people_count=people_count
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            await conn.commit()

        return result.inserted_primary_key[0]

    @classmethod
    async def get_top_times(cls, limit: int = 8) -> list[str]:
        query = (
            sa.select(cls.time_book, sa.func.count(cls.time_book).label("count"))
            .group_by(cls.time_book)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return [str(row.time_book)[:-3] for row in result.all()]

    @classmethod
    async def get_booking(cls, venue_id: int, user_id: int, date_book: date) -> t.Optional[t.Self]:
        """Находим бронь пользователя"""

        query = sa.select(cls).where(
            cls.venue_id == venue_id,
            cls.user_id == user_id,
            cls.date_book == date_book,
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            booking = result.scalars().first()
        return booking

    @classmethod
    async def get_last_book_day(cls, date_book: date) -> t.Optional[t.Self]:
        """Находим бронь пользователя"""

        query = sa.select(cls).where(cls.date_book == date_book).order_by(sa.desc(cls.gs_row))

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().first()

    @classmethod
    async def update(
            cls,
            book_id: int,
            qr_id: str = None,
            gs_row: int = None,
            status: str = None,
            is_active: bool = None
    ) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == book_id).values(updated_at=now)

        if qr_id:
            query = query.values(qr_id=qr_id)

        if gs_row:
            query = query.values(gs_row=gs_row)

        if status:
            query = query.values(status=status)

        if is_active is not None:
            query = query.values(is_active=is_active)

        async with begin_connection() as conn:
            await conn.execute(query)

    @classmethod
    async def get_booking_count(cls, venue_id: int, date_book: date, time_book: time) -> int:
        """Возвращает количество броней в заведении за 3 часа до и после указанного времени"""

        # Определяем границы временного интервала
        min_time = (datetime.combine(date_book, time_book) - timedelta(hours=3)).time()
        max_time = (datetime.combine(date_book, time_book) + timedelta(hours=3)).time()

        query = (
            sa.select(sa.func.count())
            .where(
                (cls.venue_id == venue_id) &
                (cls.date_book == date_book) &
                (cls.time_book >= min_time) &
                (cls.time_book <= max_time)
            )
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return result.scalar() or 0  # Если нет броней, возвращаем 0

    @classmethod
    async def get_booking_with_venue(cls, book_id: int) -> t.Optional[t.Self]:
        """Получает бронь по ID вместе с данными о заведении"""

        query = (
            sa.select(cls)
            .options(joinedload(cls.venue))  # подтягиваем связанную модель
            .where(cls.id == book_id)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().first()
