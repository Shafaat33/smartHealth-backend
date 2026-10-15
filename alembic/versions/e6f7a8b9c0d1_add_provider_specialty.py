"""add provider specialty and bio

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8902b
Create Date: 2026-10-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8902b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

provider_specialty = sa.Enum(
    "family_medicine",
    "cardiology",
    "dermatology",
    "orthopedics",
    "gastroenterology",
    "endocrinology",
    "pediatrics",
    "obgyn",
    "mental_health",
    name="provider_specialty",
)


def upgrade() -> None:
    provider_specialty.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "providers",
        sa.Column(
            "specialty",
            provider_specialty,
            nullable=False,
            server_default="family_medicine",
        ),
    )
    op.add_column("providers", sa.Column("bio", sa.Text(), nullable=True))
    op.create_index("ix_providers_specialty", "providers", ["specialty"])


def downgrade() -> None:
    op.drop_index("ix_providers_specialty", table_name="providers")
    op.drop_column("providers", "bio")
    op.drop_column("providers", "specialty")
    provider_specialty.drop(op.get_bind(), checkfirst=True)
