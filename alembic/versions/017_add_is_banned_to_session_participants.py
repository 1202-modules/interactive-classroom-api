"""Add is_banned to session_participants

Revision ID: 017
Revises: 016
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'session_participants',
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('session_participants', 'is_banned')
