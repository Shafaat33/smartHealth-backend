"""add confirmed appointment status

Revision ID: d5e6f7a8902b
Revises: c4d5e6f8091a
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d5e6f7a8902b"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f8091a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'confirmed'")


def downgrade() -> None:
    op.execute("UPDATE appointments SET status = 'pending' WHERE status = 'confirmed'")
