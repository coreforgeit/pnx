from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())

    event_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("events.id"))
    user_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("users.id"))
    option_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("events_options.id"))
    # pay_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("options.id"))
    pay_id: Mapped[int] = mapped_column(sa.Integer(), nullable=True)

    qr_id: Mapped[str] = mapped_column(sa.String(), nullable=True)
    gs_row: Mapped[int] = mapped_column(sa.Integer(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String())
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.true())

    event: Mapped["Event"] = relationship("Event", backref="ticket")
    user: Mapped["User"] = relationship("User", backref="ticket")
    option: Mapped["EventOption"] = relationship("EventOption", backref="ticket")

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
            gs_row: int = None,
            status: str = None,
            pay_id: bool = None,
    ) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == ticket_id).values(updated_at=now)

        if qr_id:
            query = query.values(qr_id=qr_id)

        if gs_row:
            query = query.values(gs_row=gs_row)

        if status:
            query = query.values(status=status)

        if pay_id:
            query = query.values(pay_id=pay_id)

        async with begin_connection() as conn:
            await conn.execute(query)

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
