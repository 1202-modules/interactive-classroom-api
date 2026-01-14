"""Add pending_registrations table

Revision ID: 003
Revises: 002
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pending_registrations table."""
    op.create_table(
        'pending_registrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('verification_code', sa.String(), nullable=False),
        sa.Column('verification_code_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pending_registrations_id'), 'pending_registrations', ['id'], unique=False)
    op.create_index(op.f('ix_pending_registrations_email'), 'pending_registrations', ['email'], unique=True)
    op.create_index(op.f('ix_pending_registrations_expires_at'), 'pending_registrations', ['verification_code_expires_at'], unique=False)


def downgrade() -> None:
    """Drop pending_registrations table."""
    op.drop_index(op.f('ix_pending_registrations_expires_at'), table_name='pending_registrations')
    op.drop_index(op.f('ix_pending_registrations_email'), table_name='pending_registrations')
    op.drop_index(op.f('ix_pending_registrations_id'), table_name='pending_registrations')
    op.drop_table('pending_registrations')

