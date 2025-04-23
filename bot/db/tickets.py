from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from .events import Event


class TicketStatRow(t.Protocol):
    event_id: int
    event_name: str
    ticket_count: int


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())

    event_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("events.id"))
    user_id: Mapped[int] = mapped_column(sa.BigInteger(), sa.ForeignKey("users.id"))
    option_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("events_options.id"))
    # pay_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("options.id"))
    pay_id: Mapped[int] = mapped_column(sa.Integer(), nullable=True)

    qr_id: Mapped[str] = mapped_column(sa.String(), nullable=True)
    gs_sheet: Mapped[int] = mapped_column(sa.String(), nullable=True)
    gs_page: Mapped[int] = mapped_column(sa.BigInteger(), nullable=True)
    gs_row: Mapped[int] = mapped_column(sa.Integer(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String())
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.true())

    event: Mapped["Event"] = relationship("Event", backref="ticket")
    user: Mapped["User"] = relationship("User", backref="ticket")
    option: Mapped["EventOption"] = relationship("EventOption", backref="ticket")

    @classmethod
    def _get_full_ticket_query(cls,) -> sa.select:
        return (
            sa.select(cls).options(
                joinedload(cls.event).joinedload(Event.venue),
                joinedload(cls.option)
            )
        )

    @classmethod
    async def add(
            cls,
            event_id: int,
            user_id: int,
            option_id: int,
            status: str,
    ) -> int:
        """Добавляет билет к событию"""
        now = datetime.now()
        query = sa.insert(cls).values(
            event_id=event_id,
            user_id=user_id,
            option_id=option_id,
            status=status,
            created_at=now,
            updated_at=now,
        )
        async with begin_connection() as conn:
            result = await conn.execute(query)
            await conn.commit()

        return result.inserted_primary_key[0]

    @classmethod
    async def get_all(cls, user_id: int = None) -> t.Optional[list[t.Self]]:
        query = sa.select(cls)
        if user_id:
            query = query.where(cls.user_id == user_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().all()

    @classmethod
    async def update(
            cls,
            ticket_id: int,
            qr_id: str = None,
            gs_sheet: str = None,
            gs_page: int = None,
            gs_row: int = None,
            status: str = None,
            pay_id: bool = None,
    ) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == ticket_id).values(updated_at=now)

        if qr_id:
            query = query.values(qr_id=qr_id)

        if gs_sheet:
            query = query.values(gs_sheet=gs_sheet)

        if gs_page:
            query = query.values(gs_page=gs_page)

        if gs_row:
            query = query.values(gs_row=gs_row)

        if status:
            query = query.values(status=status)

        if pay_id:
            query = query.values(pay_id=pay_id)

        async with begin_connection() as conn:
            await conn.execute(query)
            await conn.commit()

    @classmethod
    async def get_max_event_row(cls, event_id: int) -> int:
        query = (
            sa.select(sa.func.max(cls.gs_row))
            .where(cls.event_id == event_id)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            max_row = result.scalar()

        return max_row + 1 if max_row else 2

    @classmethod
    async def get_all_tickets(cls, user_id: int = None, event_id: int = None) -> t.Optional[list[t.Self]]:
        """Получает все билеты пользователя с подгрузкой event, venue и option"""

        query = cls._get_full_ticket_query()

        if user_id:
            query = query.where(cls.user_id == user_id)

        if event_id:
            query = query.where(cls.event_id == event_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_full_ticket(cls, ticket_id: int) -> t.Optional[t.Self]:
        """Получает один билет с подгрузкой event, venue и option"""
        query = cls._get_full_ticket_query().where(cls.id == ticket_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().first()

    @classmethod
    async def get_active_event_ticket_stats(cls, venue_id: int | None = None) -> list[TicketStatRow]:
        query = (
            sa.select(
                cls.event_id,
                Event.name.label("event_name"),
                sa.func.count(cls.id).label("ticket_count")
            )
            .join(Event, cls.event_id == Event.id)
            .where(cls.is_active.is_(True), Event.is_active.is_(True))
            .group_by(cls.event_id, Event.name)
            .order_by(Event.name)
        )

        # Фильтрация по venue_id (если передан)
        if venue_id:
            query = query.where(Event.venue_id == venue_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return result.all()


