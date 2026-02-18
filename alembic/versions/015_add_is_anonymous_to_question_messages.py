"""Add is_anonymous to session_question_messages

Revision ID: 015
Revises: 014
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'session_question_messages',
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('session_question_messages', 'is_anonymous')
