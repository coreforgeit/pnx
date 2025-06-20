from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from settings import conf
from enums import UserStatus


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    creator_id: Mapped[int] = mapped_column(sa.BigInteger)
    venue_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("venues.id"))
    time_event: Mapped[time] = mapped_column(sa.Time())
    date_event: Mapped[date] = mapped_column(sa.Date())
    link: Mapped[str] = mapped_column(sa.String(), nullable=True)
    name: Mapped[str] = mapped_column(sa.String())
    text: Mapped[str] = mapped_column(sa.Text(), nullable=True)
    entities: Mapped[str] = mapped_column(sa.Text(), nullable=True)
    photo_id: Mapped[str] = mapped_column(sa.String(), nullable=True)
    gs_page: Mapped[int] = mapped_column(sa.BigInteger(), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.true())

    close_msg: Mapped[str] = mapped_column(sa.Text(), nullable=True)
    close_msg_entities: Mapped[str] = mapped_column(sa.Text(), nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", backref="event")

    def time_str(self) -> str:
        return self.time_event.strftime(conf.time_format)

    def date_str(self) -> str:
        return self.date_event.strftime(conf.date_format)

    @classmethod
    async def add(
            cls,
            creator_id: int,
            venue_id: int,
            time_event: time,
            date_event: date,
            name: str,
            text: str,
            entities: str,
            photo_id: str,
            close_msg: str,
            close_msg_entities: str,
            event_id: int | None = None  # опциональный ID для обновления
    ) -> int:
        """Добавляет или обновляет событие"""
        now = datetime.now()

        insert_data = {
            "id": event_id,
            "creator_id": creator_id,
            "venue_id": venue_id,
            "time_event": time_event,
            "date_event": date_event,
            "name": name,
            "text": text,
            "entities": entities,
            "photo_id": photo_id,
            "close_msg": close_msg,
            "close_msg_entities": close_msg_entities,
            "created_at": now,
            "updated_at": now,
        }

        # Убираем ключ id, если он None (чтобы не мешал автоинкременту)
        if not event_id:
            insert_data.pop("id")

        query = (
            psql.insert(cls)
            .values(insert_data)
            .on_conflict_do_update(
                index_elements=[cls.id],
                set_={
                    "updated_at": now,
                    # "creator_id": creator_id,
                    "venue_id": venue_id,
                    "time_event": time_event,
                    "date_event": date_event,
                    "name": name,
                    "text": text,
                    "entities": entities,
                    "photo_id": photo_id,
                    "close_msg": close_msg,
                    "close_msg_entities": close_msg_entities,
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
            sa.select(cls.time_event, sa.func.count(cls.time_event).label("count"))
            .group_by(cls.time_event)
            .order_by(sa.desc("count"))
            .limit(limit)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return [str(row.time_event)[:-3] for row in result.all()]

    @classmethod
    async def update(
            cls,
            event_id: int,
            page_id: int = None,
            link: str = None,
            is_active: bool = None
    ) -> None:
        now = datetime.now()
        query = sa.update(cls).where(cls.id == event_id).values(updated_at=now)

        if page_id:
            query = query.values(gs_page=page_id)

        if link:
            query = query.values(link=link)

        if is_active is not None:
            query = query.values(is_active=is_active)

        async with begin_connection() as conn:
            await conn.execute(query)
            await conn.commit()

    @classmethod
    async def get_event_with_venue(cls, event_id: int) -> t.Optional[t.Self]:
        """Получает бронь по ID вместе с данными о заведении"""

        query = (
            sa.select(cls)
            .options(joinedload(cls.venue))  # подтягиваем связанную модель
            .where(cls.id == event_id)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().first()

    @classmethod
    async def close_old(cls) -> None:
        today = datetime.now(tz=conf.tz).date()
        print(f'event today: {today}')
        query = (
            sa.update(cls).
            where(cls.date_event < today, cls.is_active == True).
            values(is_active=False)
        )
        async with begin_connection() as conn:
            await conn.execute(query)
