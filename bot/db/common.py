from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import aliased
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
import typing as t

from .base import Base
from .books import Book
from .tickets import Ticket
from .events import Event
from .venues import Venue


async def get_available_tables(
        venue_id: int,
        book_date: date,
        book_time: time,
        session: AsyncSession,
) -> int:
    """Возвращает количество свободных столов в заведении на указанное время"""

    # Получаем количество занятых броней
    booked_count = await Book.get_booking_count(
        session=session,
        venue_id=venue_id,
        date_book=book_date,
        time_book=book_time,
    )

    # Запрос количества столов в заведении
    query = sa.select(Venue.table_count).where(Venue.id == venue_id)

    result = await session.execute(query)
    table_count = result.scalar()

    # Если данных нет, значит заведение не найдено
    if not table_count:
        raise ValueError(f"Заведение с id {venue_id} не найдено")

    return table_count - booked_count


# отменяет брони и закрывает ивенты если не сработал обычный тригер
async def close_old(session: AsyncSession):
    await Book.close_old(session=session)
    await Ticket.close_old(session=session)
    await Event.close_old(session=session)
