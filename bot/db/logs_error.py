from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection


class LogsError(Base):
    __tablename__ = "logs_error"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    user_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=True)
    traceback: Mapped[str] = mapped_column(sa.Text, nullable=True)
    message: Mapped[str] = mapped_column(sa.Text, nullable=True)
    comment: Mapped[str] = mapped_column(sa.String, nullable=True)


    @classmethod
    async def add(cls, user_id: int, traceback: str, message: str) -> None:
        query = sa.insert(cls).values(user_id=user_id, traceback=traceback, message=message)

        async with begin_connection() as conn:
            await conn.execute(query)
            await conn.commit()
