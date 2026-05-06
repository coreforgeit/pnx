"""initial schema

Revision ID: 43273437e9c9
Revises:
Create Date: 2026-04-27 14:19:27.724076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "43273437e9c9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create application tables."""
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("time_open", sa.Time(), nullable=False),
        sa.Column("time_close", sa.Time(), server_default=sa.text("'23:59'"), nullable=False),
        sa.Column("table_count", sa.Integer(), nullable=False),
        sa.Column("book_len", sa.Integer(), server_default=sa.text("180"), nullable=False),
        sa.Column("book_gs_id", sa.String(), nullable=True),
        sa.Column("event_gs_id", sa.String(), nullable=True),
        sa.Column("admin_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("first_visit", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_visit", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="user", nullable=False),
        sa.Column("mailing", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("creator_id", sa.BigInteger(), nullable=False),
        sa.Column("venue_id", sa.Integer(), nullable=False),
        sa.Column("time_event", sa.Time(), nullable=False),
        sa.Column("date_event", sa.Date(), nullable=False),
        sa.Column("link", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("entities", sa.Text(), nullable=True),
        sa.Column("photo_id", sa.String(), nullable=True),
        sa.Column("gs_page", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("close_msg", sa.Text(), nullable=True),
        sa.Column("close_msg_entities", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("venue_id", sa.Integer(), nullable=False),
        sa.Column("time_book", sa.Time(), nullable=False),
        sa.Column("date_book", sa.Date(), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("qr_id", sa.String(), nullable=True),
        sa.Column("gs_row", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "events_options",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("all_place", sa.Integer(), nullable=False),
        sa.Column("empty_place", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("gs_row", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("pay_id", sa.String(), nullable=True),
        sa.Column("qr_id", sa.String(), nullable=True),
        sa.Column("gs_sheet", sa.String(), nullable=True),
        sa.Column("gs_page", sa.BigInteger(), nullable=True),
        sa.Column("gs_row", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["option_id"], ["events_options.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("store_id", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("invoice_id", sa.String(length=255), nullable=False),
        sa.Column("invoice_uuid", sa.String(length=255), nullable=False),
        sa.Column("billing_id", sa.String(length=255), nullable=True),
        sa.Column("payment_time", sa.DateTime(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("card_pan", sa.String(length=20), nullable=False),
        sa.Column("card_token", sa.String(length=255), nullable=False),
        sa.Column("ps", sa.String(length=50), nullable=False),
        sa.Column("uuid", sa.String(length=255), nullable=False),
        sa.Column("receipt_url", sa.String(length=2048), nullable=False),
        sa.Column("tickets", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "logs_admin",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "logs_error",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop application tables."""
    op.drop_table("logs_error")
    op.drop_table("logs_admin")
    op.drop_table("payments")
    op.drop_table("tickets")
    op.drop_table("events_options")
    op.drop_table("books")
    op.drop_table("events")
    op.drop_table("users")
    op.drop_table("venues")
