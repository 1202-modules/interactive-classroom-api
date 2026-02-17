"""Remove verified_until from guest_email_verifications

Revision ID: 009
Revises: 008
Create Date: 2025-02-17

Expiration is handled by JWT exp; record exists = not revoked.
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_guest_email_verifications_verified_until",
        table_name="guest_email_verifications",
    )
    op.drop_column("guest_email_verifications", "verified_until")


def downgrade() -> None:
    op.add_column(
        "guest_email_verifications",
        sa.Column("verified_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE guest_email_verifications SET verified_until = updated_at + interval '24 hours'"
        )
    )
    op.alter_column(
        "guest_email_verifications",
        "verified_until",
        nullable=False,
    )
    op.create_index(
        "ix_guest_email_verifications_verified_until",
        "guest_email_verifications",
        ["verified_until"],
        unique=False,
    )
