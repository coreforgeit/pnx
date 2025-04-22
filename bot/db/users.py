from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from enums import UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    first_visit: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    last_visit: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    full_name: Mapped[str] = mapped_column(sa.String)
    username: Mapped[str] = mapped_column(sa.String, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(), server_default=UserStatus.USER.value)
    mailing: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.true())
    venue_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("venues.id"), nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", backref="user")

    @classmethod
    async def add(cls, user_id: int, full_name: str, username: str) -> None:
        """Добавляет новую запись в таблицу users"""
        now = datetime.now()
        query = (
            psql.insert(cls)
            .values(
                first_visit=now,
                last_visit=now,
                id=user_id,
                full_name=full_name,
                username=username,
            ).on_conflict_do_update(
                index_elements=[cls.id],
                set_={"full_name": full_name, 'username': username, 'last_visit': now}
            )
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            await conn.commit()
        return result.inserted_primary_key[0]

    @classmethod
    async def update(
            cls,
            user_id: int,
            mailing: bool = None,
            status: str = None,
            venue_id: int = None,
    ) -> None:

        query = sa.update(cls).where(cls.id == user_id)

        if mailing:
            query = query.values(mailing=mailing)

        if status:
            query = query.values(status=status)

        if venue_id:
            query = query.values(venue_id=venue_id)

        async with begin_connection() as conn:
            await conn.execute(query)
            await conn.commit()

    @classmethod
    async def get_admin(cls, user_id: int) -> t.Optional[t.Self]:

        query = (
            sa.select(cls)
            .options(joinedload(cls.venue))  # подтягиваем связанную модель
            .where(cls.id == user_id)
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            return result.scalars().first()

    @classmethod
    async def get_all_users(cls, for_mailing: bool = False) -> list[t.Self]:

        query = sa.select(cls).where(cls.status == UserStatus.USER.value)

        if for_mailing:
            query = query.where(cls.mailing == True)

        async with begin_connection() as conn:
            result = await conn.execute(query)
        return result.scalars().all()
