"""Add modules tables and passcode to sessions

Revision ID: 007
Revises: 006
Create Date: 2025-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import random
import string

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def generate_passcode() -> str:
    """Generate a random 6-character alphanumeric passcode."""
    characters = string.ascii_uppercase + string.digits
    # Exclude confusing characters
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(random.choices(characters, k=6))


def upgrade() -> None:
    """Add modules tables and passcode to sessions."""
    
    # === Create workspace_modules table ===
    op.create_table(
        'workspace_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('module_type', sa.String(), nullable=False),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workspace_modules_workspace_id', 'workspace_modules', ['workspace_id'], unique=False)
    op.create_index('ix_workspace_modules_is_deleted', 'workspace_modules', ['is_deleted'], unique=False)
    
    # === Create session_modules table ===
    op.create_table(
        'session_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('module_type', sa.String(), nullable=False),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_session_modules_session_id', 'session_modules', ['session_id'], unique=False)
    op.create_index('ix_session_modules_is_deleted', 'session_modules', ['is_deleted'], unique=False)
    op.create_index('ix_session_modules_is_active', 'session_modules', ['is_active'], unique=False)
    
    # Create partial unique constraint: only one active module per session
    op.execute("""
        CREATE UNIQUE INDEX uq_session_modules_one_active 
        ON session_modules (session_id) 
        WHERE is_active = true
    """)
    
    # === Add passcode to sessions table ===
    op.add_column('sessions', sa.Column('passcode', sa.String(length=6), nullable=True))
    op.create_index('ix_sessions_passcode', 'sessions', ['passcode'], unique=True)
    
    # Generate passcodes for existing sessions
    # Get all existing sessions
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM sessions"))
    session_ids = [row[0] for row in result]
    
    # Generate unique passcodes for each session
    used_passcodes = set()
    for session_id in session_ids:
        # Generate unique passcode
        while True:
            passcode = generate_passcode()
            if passcode not in used_passcodes:
                # Check if it exists in database
                check_result = connection.execute(
                    sa.text("SELECT COUNT(*) FROM sessions WHERE passcode = :passcode"),
                    {"passcode": passcode}
                )
                if check_result.scalar() == 0:
                    used_passcodes.add(passcode)
                    break
        
        # Update session with passcode
        connection.execute(
            sa.text("UPDATE sessions SET passcode = :passcode WHERE id = :id"),
            {"passcode": passcode, "id": session_id}
        )
    
    # Make passcode NOT NULL after generating for all existing sessions
    op.alter_column('sessions', 'passcode', nullable=False)
    
    # === Add active_module_id to sessions table ===
    op.add_column('sessions', sa.Column('active_module_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sessions_active_module_id',
        'sessions', 'session_modules',
        ['active_module_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Revert modules tables and passcode from sessions."""
    
    # === Remove active_module_id from sessions ===
    op.drop_constraint('fk_sessions_active_module_id', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'active_module_id')
    
    # === Remove passcode from sessions ===
    op.drop_index('ix_sessions_passcode', table_name='sessions')
    op.drop_column('sessions', 'passcode')
    
    # === Drop session_modules table ===
    op.drop_index('uq_session_modules_one_active', table_name='session_modules')
    op.drop_index('ix_session_modules_is_active', table_name='session_modules')
    op.drop_index('ix_session_modules_is_deleted', table_name='session_modules')
    op.drop_index('ix_session_modules_session_id', table_name='session_modules')
    op.drop_table('session_modules')
    
    # === Drop workspace_modules table ===
    op.drop_index('ix_workspace_modules_is_deleted', table_name='workspace_modules')
    op.drop_index('ix_workspace_modules_workspace_id', table_name='workspace_modules')
    op.drop_table('workspace_modules')

