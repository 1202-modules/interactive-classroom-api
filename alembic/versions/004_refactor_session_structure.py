"""Refactor session structure and remove workspace computed fields

Revision ID: 004
Revises: 003
Create Date: 2025-01-15 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Refactor session structure and remove workspace computed fields."""
    
    # === Sessions table changes ===
    
    # Add end_datetime column
    op.add_column('sessions', sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=True))
    
    # Rename participant_count to stopped_participant_count
    op.alter_column('sessions', 'participant_count', new_column_name='stopped_participant_count')
    
    # Change status default from 'draft' to 'active'
    op.alter_column('sessions', 'status', server_default='active')
    
    # Update existing 'draft' sessions to 'active'
    op.execute("UPDATE sessions SET status = 'active' WHERE status = 'draft'")
    
    # Update existing 'ended' sessions: set end_datetime from updated_at, set status to 'active'
    op.execute("""
        UPDATE sessions 
        SET end_datetime = updated_at, status = 'active' 
        WHERE status = 'ended' AND updated_at IS NOT NULL
    """)
    
    # For 'ended' sessions without updated_at, just set status to 'active'
    op.execute("UPDATE sessions SET status = 'active' WHERE status = 'ended'")
    
    # === Workspaces table changes ===
    
    # Drop computed fields
    op.drop_column('workspaces', 'session_count')
    op.drop_column('workspaces', 'participant_count')
    op.drop_column('workspaces', 'last_session_at')


def downgrade() -> None:
    """Revert session structure refactoring."""
    
    # === Workspaces table changes (revert) ===
    
    # Add back computed fields with defaults
    op.add_column('workspaces', sa.Column('session_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('workspaces', sa.Column('participant_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('workspaces', sa.Column('last_session_at', sa.DateTime(timezone=True), nullable=True))
    
    # === Sessions table changes (revert) ===
    
    # Revert status changes: 'active' sessions without end_datetime become 'draft'
    op.execute("""
        UPDATE sessions 
        SET status = 'draft' 
        WHERE status = 'active' AND start_datetime IS NULL
    """)
    
    # Revert status changes: 'active' sessions with end_datetime become 'ended'
    op.execute("""
        UPDATE sessions 
        SET status = 'ended' 
        WHERE status = 'active' AND end_datetime IS NOT NULL
    """)
    
    # Change status default back to 'draft'
    op.alter_column('sessions', 'status', server_default='draft')
    
    # Rename stopped_participant_count back to participant_count
    op.alter_column('sessions', 'stopped_participant_count', new_column_name='participant_count')
    
    # Drop end_datetime column
    op.drop_column('sessions', 'end_datetime')

