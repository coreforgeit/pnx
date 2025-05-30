from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from datetime import datetime, timedelta, date, time
from sqlalchemy.dialects import postgresql as psql

import sqlalchemy as sa
import typing as t

from .base import Base, begin_connection
from settings import conf
from enums import UserStatus


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(), server_default=sa.func.now())

    user_id: Mapped[t.Optional[int]] = mapped_column(sa.BigInteger, sa.ForeignKey("users.id"), nullable=True)

    store_id: Mapped[str] = mapped_column(sa.String(50))
    amount: Mapped[int] = mapped_column(sa.BigInteger)
    invoice_id: Mapped[str] = mapped_column(sa.String(255))
    invoice_uuid: Mapped[str] = mapped_column(sa.String(255))
    billing_id: Mapped[t.Optional[str]] = mapped_column(sa.String(255), nullable=True)
    payment_time: Mapped[datetime] = mapped_column(sa.DateTime)
    phone: Mapped[str] = mapped_column(sa.String(20))
    card_pan: Mapped[str] = mapped_column(sa.String(20))
    card_token: Mapped[str] = mapped_column(sa.String(255))
    ps: Mapped[str] = mapped_column(sa.String(50))
    uuid: Mapped[str] = mapped_column(sa.String(255))
    receipt_url: Mapped[str] = mapped_column(sa.String(2048))
    tickets: Mapped[t.List[int]] = mapped_column(psql.ARRAY(sa.Integer), default=list)

    def __repr__(self):
        return f"<Payment #{self.id} — {self.amount} сум>"
