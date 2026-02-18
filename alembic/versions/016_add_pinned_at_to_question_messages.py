"""Add pinned_at to session_question_messages

Revision ID: 016
Revises: 015
Create Date: 2025-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'session_question_messages',
        sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('session_question_messages', 'pinned_at')
