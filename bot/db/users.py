from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from enums import UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    first_visit: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    last_visit: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    full_name: Mapped[str] = mapped_column(sa.String)
    username: Mapped[str] = mapped_column(sa.String, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(), default=UserStatus.USER.value)
    mailing: Mapped[bool] = mapped_column(sa.Boolean, default=True)

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
            return result.inserted_primary_key[0]

    @classmethod
    async def update(
            cls,
            user_id: int,
            mailing: bool = None,
            status: str = None
    ) -> None:

        query = sa.update(cls).where(cls.id == user_id)

        if mailing:
            query = query.values(mailing=mailing)

        if status:
            query = query.values(status=status)

        async with begin_connection() as conn:
            await conn.execute(query)
