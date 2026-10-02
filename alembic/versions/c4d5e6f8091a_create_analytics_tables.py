"""create analytics tables

Revision ID: c4d5e6f8091a
Revises: b3c4d5e6f708
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f8091a"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f708"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_daily",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("booked", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("canceled", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("day"),
    )
    op.create_table(
        "analytics_events",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("analytics_daily")
