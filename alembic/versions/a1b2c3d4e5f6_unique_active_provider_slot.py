"""unique active provider appointment slot

Revision ID: a1b2c3d4e5f6
Revises: 77dfff7161d0
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "77dfff7161d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_provider_slot",
        "appointments",
        ["provider_id", "appointment_time"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('complete', 'canceled')"),
    )


def downgrade() -> None:
    op.drop_index("uq_provider_slot", table_name="appointments")
