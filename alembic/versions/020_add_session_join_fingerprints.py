"""Add session_join_fingerprints table

Revision ID: 020
Revises: 019
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_join_fingerprints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=64), nullable=False),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_session_join_fingerprints_id",
        "session_join_fingerprints",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_session_join_fingerprints_session_hash_entry",
        "session_join_fingerprints",
        ["session_id", "fingerprint_hash", "entry_type"],
        unique=False,
    )
    op.create_index(
        "ix_session_join_fingerprints_created_at",
        "session_join_fingerprints",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_session_join_fingerprints_created_at",
        table_name="session_join_fingerprints",
    )
    op.drop_index(
        "ix_session_join_fingerprints_session_hash_entry",
        table_name="session_join_fingerprints",
    )
    op.drop_index(
        "ix_session_join_fingerprints_id",
        table_name="session_join_fingerprints",
    )
    op.drop_table("session_join_fingerprints")
