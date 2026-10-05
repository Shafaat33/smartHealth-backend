"""create ai conversation tables

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2026-10-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "g8h9i0j1k2l3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ai_message_role = postgresql.ENUM(
    "user", "assistant", name="ai_message_role", create_type=False
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE ai_message_role AS ENUM ('user', 'assistant');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("ai_conversations"):
        op.create_table(
            "ai_conversations",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])
    if not insp.has_table("ai_messages"):
        op.create_table(
            "ai_messages",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("conversation_id", sa.UUID(), nullable=False),
            sa.Column("role", ai_message_role, nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("intent", sa.String(length=32), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("sources", sa.JSON(), nullable=True),
            sa.Column("suggestion", sa.JSON(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_messages_conversation_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_user_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
    op.execute("DROP TYPE IF EXISTS ai_message_role")
