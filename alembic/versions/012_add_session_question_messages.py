"""Add session_question_messages and session_question_message_likes tables

Revision ID: 012
Revises: 011
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_question_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_module_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_answered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_module_id"], ["session_modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["session_participants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["session_question_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_question_messages_session_module_id", "session_question_messages", ["session_module_id"], unique=False)
    op.create_index("ix_session_question_messages_participant_id", "session_question_messages", ["participant_id"], unique=False)
    op.create_index("ix_session_question_messages_parent_id", "session_question_messages", ["parent_id"], unique=False)
    op.create_index("ix_session_question_messages_is_deleted", "session_question_messages", ["is_deleted"], unique=False)

    op.create_table(
        "session_question_message_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["session_question_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["session_participants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_question_message_likes_message_id", "session_question_message_likes", ["message_id"], unique=False)
    op.create_index("ix_session_question_message_likes_participant_id", "session_question_message_likes", ["participant_id"], unique=False)
    op.create_unique_constraint(
        "uq_session_question_message_likes_message_participant",
        "session_question_message_likes",
        ["message_id", "participant_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_session_question_message_likes_message_participant", "session_question_message_likes", type_="unique")
    op.drop_index("ix_session_question_message_likes_participant_id", table_name="session_question_message_likes")
    op.drop_index("ix_session_question_message_likes_message_id", table_name="session_question_message_likes")
    op.drop_table("session_question_message_likes")

    op.drop_index("ix_session_question_messages_is_deleted", table_name="session_question_messages")
    op.drop_index("ix_session_question_messages_parent_id", table_name="session_question_messages")
    op.drop_index("ix_session_question_messages_participant_id", table_name="session_question_messages")
    op.drop_index("ix_session_question_messages_session_module_id", table_name="session_question_messages")
    op.drop_table("session_question_messages")
