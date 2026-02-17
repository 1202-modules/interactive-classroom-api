"""Add session_module_timer_state table

Revision ID: 013
Revises: 012
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_module_timer_state",
        sa.Column("session_module_id", sa.Integer(), nullable=False),
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remaining_seconds", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_module_id"], ["session_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_module_id"),
    )


def downgrade() -> None:
    op.drop_table("session_module_timer_state")
