from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from enums import UserStatus


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())
    name: Mapped[str] = mapped_column(sa.String)
    time_open: Mapped[time] = mapped_column(sa.Time)
    time_close: Mapped[time] = mapped_column(sa.Time, server_default='23:59')
    table_count: Mapped[int] = mapped_column(sa.Integer)
    book_len: Mapped[int] = mapped_column(sa.Integer, server_default='180')
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=True)

