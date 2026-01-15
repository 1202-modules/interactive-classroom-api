"""Add is_stopped flag, refactor session settings with templates

Revision ID: 005
Revises: 004
Create Date: 2025-01-15 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_stopped flag, refactor session settings with templates."""
    
    # === Sessions table changes ===
    
    # Add is_stopped column
    op.add_column('sessions', sa.Column('is_stopped', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_sessions_is_stopped', 'sessions', ['is_stopped'], unique=False)
    
    # Add template_link_type column
    op.add_column('sessions', sa.Column('template_link_type', sa.String(), nullable=False, server_default='full'))
    
    # Add custom_settings column
    op.add_column('sessions', sa.Column('custom_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Update existing sessions: set is_stopped based on end_datetime
    op.execute("UPDATE sessions SET is_stopped = (end_datetime IS NOT NULL)")
    
    # Update existing sessions: set template_link_type = 'full', custom_settings = NULL
    op.execute("UPDATE sessions SET template_link_type = 'full', custom_settings = NULL")
    
    # === Workspaces table changes ===
    
    # Rename session_settings to template_settings
    op.alter_column('workspaces', 'session_settings', new_column_name='template_settings')


def downgrade() -> None:
    """Revert session settings template refactoring."""
    
    # === Workspaces table changes (revert) ===
    
    # Rename template_settings back to session_settings
    op.alter_column('workspaces', 'template_settings', new_column_name='session_settings')
    
    # === Sessions table changes (revert) ===
    
    # Drop custom_settings column
    op.drop_column('sessions', 'custom_settings')
    
    # Drop template_link_type column
    op.drop_column('sessions', 'template_link_type')
    
    # Drop is_stopped column and index
    op.drop_index('ix_sessions_is_stopped', table_name='sessions')
    op.drop_column('sessions', 'is_stopped')

