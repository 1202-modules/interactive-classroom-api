"""Add guest_email_verifications and session_pending_email_codes tables

Revision ID: 008
Revises: 007
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guest_email_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("verified_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_guest_email_verifications_email",
        "guest_email_verifications",
        ["email"],
        unique=True,
    )
    op.create_index(
        "ix_guest_email_verifications_verified_until",
        "guest_email_verifications",
        ["verified_until"],
        unique=False,
    )

    op.create_table(
        "session_pending_email_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "email", name="uq_session_pending_email_code_session_email"),
    )
    op.create_index(
        "ix_session_pending_email_codes_session_id",
        "session_pending_email_codes",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_session_pending_email_codes_email",
        "session_pending_email_codes",
        ["email"],
        unique=False,
    )
    op.create_index(
        "ix_session_pending_email_codes_expires_at",
        "session_pending_email_codes",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_session_pending_email_codes_expires_at",
        table_name="session_pending_email_codes",
    )
    op.drop_index(
        "ix_session_pending_email_codes_email",
        table_name="session_pending_email_codes",
    )
    op.drop_index(
        "ix_session_pending_email_codes_session_id",
        table_name="session_pending_email_codes",
    )
    op.drop_table("session_pending_email_codes")

    op.drop_index(
        "ix_guest_email_verifications_verified_until",
        table_name="guest_email_verifications",
    )
    op.drop_index(
        "ix_guest_email_verifications_email",
        table_name="guest_email_verifications",
    )
    op.drop_table("guest_email_verifications")
