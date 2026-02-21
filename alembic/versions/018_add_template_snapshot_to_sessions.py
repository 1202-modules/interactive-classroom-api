"""Add template_snapshot to sessions (freeze workspace template at creation)

Revision ID: 018
Revises: 017
Create Date: 2025-02-20

Session settings are merged from template_snapshot + custom_settings.
When null (existing sessions), workspace template is used for backward compatibility.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('template_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('sessions', 'template_snapshot')
