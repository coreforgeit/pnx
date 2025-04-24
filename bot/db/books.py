from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from settings import conf
from enums import UserStatus


class BookStatRow(t.Protocol):
    date: date
    book_count: int


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
    comment: Mapped[str] = mapped_column(sa.String(), nullable=True)
    qr_id: Mapped[str] = mapped_column(sa.String(), nullable=True)
    gs_row: Mapped[int] = mapped_column(sa.Integer(), default=2)
    status: Mapped[str] = mapped_column(sa.String())

    # is_come: Mapped[bool] = mapped_column(sa.Boolean(), default=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), default=True)

    venue: Mapped["Venue"] = relationship("Venue", backref="bookings")

    @classmethod
    def _get_query_with_venue(cls):
        return sa.select(cls).options(joinedload(cls.venue))

    def time_str(self) -> str:
        return self.time_book.strftime(conf.time_format)

    def date_str(self) -> str:
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
            people_count: int,
            book_id: int | None = None
    ) -> int:
        """Добавляет или обновляет бронь столика"""
        now = datetime.now()

        insert_data = {
            "id": book_id,
            "user_id": user_id,
            "venue_id": venue_id,
            "time_book": time_book,
            "date_book": date_book,
            "comment": comment,
            "status": status,
            "people_count": people_count,
            "created_at": now,
            "updated_at": now,
        }

        if not book_id:
            insert_data.pop("id")

        query = (
            psql.insert(cls)
            .values(insert_data)
            .on_conflict_do_update(
                index_elements=[cls.id],
                set_={
                    "user_id": user_id,
                    "venue_id": venue_id,
                    "time_book": time_book,
                    "date_book": date_book,
                    "comment": comment,
                    "status": status,
                    "people_count": people_count,
                    "updated_at": now,
                }
            )
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
            await conn.commit()

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
        return result.scalars().first()

    @classmethod
    async def get_books_by_date(cls, date_book: date) -> list[t.Self]:
        """Находим брони на дату"""

        # query = sa.select(cls).where(cls.date_book == date_book)

        query = cls._get_query_with_venue()
        query = query.where(cls.date_book == date_book, cls.is_active == True)

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_last_book_day(cls, date_book: date) -> t.Optional[t.Self]:
        """Находим бронь пользователя"""

        query = sa.select(cls).where(cls.date_book == date_book).order_by(sa.desc(cls.gs_row))

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().first()

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

        query = cls._get_query_with_venue()
        query = query.where(cls.id == book_id)
        # query = (
        #     sa.select(cls)
        #     .options(joinedload(cls.venue))  # подтягиваем связанную модель
        #     .where(cls.id == book_id)
        # )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().first()

    @classmethod
    async def get_all_user_booking(cls, user_id: int) -> t.Optional[list[t.Self]]:
        """Получает бронь по ID вместе с данными о заведении"""

        query = (
            sa.select(cls)
            .options(joinedload(cls.venue))  # подтягиваем связанную модель
            .where(cls.user_id == user_id)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_book_stats_by_date(cls, venue_id: int | None = None) -> list[BookStatRow]:

        query = (
            sa.select(
                cls.date_book.label("date"),
                sa.func.count(cls.id).label("book_count")
            )
            .where(cls.is_active.is_(True))
            .group_by(cls.date_book)
            .order_by(cls.date_book)
        )

        if venue_id is not None:
            query = query.where(cls.venue_id == venue_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return result.all()

    # @classmethod
    # async def del_booking(cls, book_id: int) -> None:
    #     """Получает бронь по ID вместе с данными о заведении"""
    #
    #     query = sa.delete(cls).where(cls.id == book_id)
    #
    #     async with begin_connection() as conn:
    #         await conn.execute(query)
    #         await conn.commit()


