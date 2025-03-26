from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from enums import UserStatus


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(), default=datetime.now())
    name: Mapped[str] = mapped_column(sa.String)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=True)

