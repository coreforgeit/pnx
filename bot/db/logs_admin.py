from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from settings import conf


class AdminLog(Base):
    __tablename__ = "logs_admin"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())
    admin_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    comment: Mapped[str] = mapped_column(sa.Text(), nullable=True)

    def __repr__(self):
        return f"<AdminLog admin_id={self.admin_id} action='{self.action}'>"

    @classmethod
    async def add(
            cls,
            admin_id: int,
            action: str,
            user_id: int = None,
            comment: str = None,
    ) -> int:
        now = datetime.now()
        query = sa.insert(cls).values(
            created_at=now,
            admin_id=admin_id,
            action=action,
            user_id=user_id,
            comment=comment,
        )

        async with begin_connection() as conn:
            result = await conn.execute(query)
            await conn.commit()

        return result.inserted_primary_key[0]
