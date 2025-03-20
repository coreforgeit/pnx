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

    @classmethod
    async def add(cls, user_id: int, full_name: str, username: str) -> None:
        """Добавляет новую запись в таблицу users"""
        now = datetime.now()
        query = (
            psql.insert(cls)
            .values(
                first_visit=now,
                last_visit=now,
                user_id=user_id,
                full_name=full_name,
                username=username,
            ).on_conflict_do_update(
                index_elements=[cls.user_id],
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
            last_check_time: datetime = None,
            is_sub: bool = None,
            plugin_hash: str = None
    ) -> None:
        """Обновляет запись в таблице users"""

        query = sa.update(cls).where(cls.user_id == user_id)

        if last_check_time:
            query = query.values(last_check_time=last_check_time, is_sub=True)

        if is_sub:
            query = query.values(is_sub=is_sub)

        if plugin_hash:
            query = query.values(plugin_hash=plugin_hash)

        async with begin_connection() as conn:
            await conn.execute(query)

    @classmethod
    async def get_by_id(cls, user_id: int) -> t.Optional[t.Self]:
        """Возвращает строку по user_id"""

        query = sa.select(cls).where(cls.user_id == user_id)

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return result.first()

    @classmethod
    async def get_for_check_sub(cls) -> t.Optional[t.Self]:
        """Последнего проверенного пользователя"""

        query = sa.select(cls).order_by(sa.desc(cls.last_check_time))

        async with begin_connection() as conn:
            result = await conn.execute(query)

        return result.first()

