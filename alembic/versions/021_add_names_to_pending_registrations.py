"""Add first_name and last_name to pending_registrations

Revision ID: 021
Revises: 020
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pending_registrations", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("pending_registrations", sa.Column("last_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("pending_registrations", "last_name")
    op.drop_column("pending_registrations", "first_name")
