from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.ext.asyncio import AsyncSession

import sqlalchemy as sa
import typing as t

from .base import Base
from settings import conf
from enums import UserStatus


class EventOption(Base):
    __tablename__ = "events_options"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    event_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("events.id"))
    name: Mapped[str] = mapped_column(sa.String())
    all_place: Mapped[int] = mapped_column(sa.Integer())
    empty_place: Mapped[int] = mapped_column(sa.Integer())
    price: Mapped[int] = mapped_column(sa.Integer(), nullable=True, default=0)
    gs_row: Mapped[int] = mapped_column(sa.Integer(), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.true())

    event: Mapped["Event"] = relationship("Event", backref="option")

    @classmethod
    async def add(
            cls,
            session: AsyncSession,
            event_id: int,
            name: str,
            all_place: int,
            price: int,
            is_active: bool = True,
            option_id: int | None = None,
            auto_commit: bool = True,
    ) -> int:
        """Добавляет или обновляет опцию (категорию мест) к событию"""
        now = datetime.now()

        insert_data = {
            "id": option_id,
            "event_id": event_id,
            "name": name,
            "all_place": all_place,
            "empty_place": all_place,  # при вставке — все места свободны
            "price": price,
            "created_at": now,
            "updated_at": now,
        }

        if option_id is None:
            insert_data.pop("id")

        query = (
            psql.insert(cls)
            .values(insert_data)
            .on_conflict_do_update(
                index_elements=[cls.id],
                set_={
                    "name": name,
                    "all_place": all_place,
                    "price": price,
                    "is_active": is_active,
                    "updated_at": now,
                }
            )
        )

        result = await session.execute(query)
        if auto_commit:
            await session.commit()

        return result.inserted_primary_key[0]

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            option_id: int,
            qr_id: str = None,
            gs_row: int = None,
            add_place: int = None,
            is_active: bool = None,
            auto_commit: bool = True,
    ) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == option_id).values(updated_at=now)

        if qr_id:
            query = query.values(qr_id=qr_id)

        if gs_row:
            query = query.values(gs_row=gs_row)

        if add_place:
            query = query.values(empty_place=cls.empty_place + add_place)

        if is_active is not None:
            query = query.values(is_active=is_active)

        await session.execute(query)
        if auto_commit:
            await session.commit()

    @classmethod
    async def get_top_names(cls, session: AsyncSession, limit: int = 8) -> list[str]:
        """Возвращает список самых популярных названий опций событий"""
        query = (
            sa.select(cls.name, sa.func.count(cls.name).label("count"))
            .group_by(cls.name)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        result = await session.execute(query)

        return [row.name for row in result.all()]

    @classmethod
    async def get_top_place(cls, session: AsyncSession, limit: int = 8) -> list[int]:
        """Возвращает список самых популярных названий опций событий"""
        query = (
            sa.select(cls.all_place, sa.func.count(cls.all_place).label("count"))
            .group_by(cls.all_place)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        result = await session.execute(query)

        return [row.all_place for row in result.all()]

    @classmethod
    async def get_top_price(cls, session: AsyncSession, limit: int = 8) -> list[int]:
        """Возвращает список самых популярных названий опций событий"""
        query = (
            sa.select(cls.price, sa.func.count(cls.price).label("count"))
            .group_by(cls.price)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        result = await session.execute(query)

        return [row.price for row in result.all()]

    @classmethod
    async def get_all(cls, session: AsyncSession, event_id: int = None) -> t.Optional[list[t.Self]]:
        query = sa.select(cls)
        if event_id:
            query = query.where(cls.event_id == event_id)

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_name_and_event_id(cls, session: AsyncSession, name: str, event_id: int) -> t.Self | None:
        query = sa.select(cls).where(cls.name == name, cls.event_id == event_id)

        result = await session.execute(query)
        return result.scalars().first()





