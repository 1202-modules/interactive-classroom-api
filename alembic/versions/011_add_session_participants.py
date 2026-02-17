"""Add session_participants table

Revision ID: 011
Revises: 010
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("participant_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("guest_email", sa.String(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("anonymous_slug", sa.String(), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_participants_session_id", "session_participants", ["session_id"], unique=False)
    op.create_index("ix_session_participants_participant_type", "session_participants", ["participant_type"], unique=False)
    op.create_index("ix_session_participants_user_id", "session_participants", ["user_id"], unique=False)
    op.create_index("ix_session_participants_guest_email", "session_participants", ["guest_email"], unique=False)
    op.create_index("ix_session_participants_anonymous_slug", "session_participants", ["anonymous_slug"], unique=False)
    op.create_index("ix_session_participants_last_heartbeat_at", "session_participants", ["last_heartbeat_at"], unique=False)
    op.create_index("ix_session_participants_is_deleted", "session_participants", ["is_deleted"], unique=False)
    op.create_index("ix_session_participants_session_user", "session_participants", ["session_id", "user_id"], unique=False)
    op.create_index("ix_session_participants_session_guest_email", "session_participants", ["session_id", "guest_email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_session_participants_session_guest_email", table_name="session_participants")
    op.drop_index("ix_session_participants_session_user", table_name="session_participants")
    op.drop_index("ix_session_participants_is_deleted", table_name="session_participants")
    op.drop_index("ix_session_participants_last_heartbeat_at", table_name="session_participants")
    op.drop_index("ix_session_participants_anonymous_slug", table_name="session_participants")
    op.drop_index("ix_session_participants_guest_email", table_name="session_participants")
    op.drop_index("ix_session_participants_user_id", table_name="session_participants")
    op.drop_index("ix_session_participants_participant_type", table_name="session_participants")
    op.drop_index("ix_session_participants_session_id", table_name="session_participants")
    op.drop_table("session_participants")
