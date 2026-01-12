"""Initial migration - create users, workspaces, sessions tables

Revision ID: 001
Revises: 
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_code', sa.String(), nullable=True),
        sa.Column('verification_code_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_is_deleted'), 'users', ['is_deleted'], unique=False)
    op.create_index(
        'ix_users_email_unique',
        'users',
        ['email'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('session_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('session_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('participant_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_session_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)
    op.create_index(op.f('ix_workspaces_user_id'), 'workspaces', ['user_id'], unique=False)
    op.create_index(op.f('ix_workspaces_status'), 'workspaces', ['status'], unique=False)
    op.create_index(op.f('ix_workspaces_is_deleted'), 'workspaces', ['is_deleted'], unique=False)
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_workspace_id'), 'sessions', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_sessions_status'), 'sessions', ['status'], unique=False)
    op.create_index(op.f('ix_sessions_is_deleted'), 'sessions', ['is_deleted'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_sessions_is_deleted'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_status'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_workspace_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    
    op.drop_index(op.f('ix_workspaces_is_deleted'), table_name='workspaces')
    op.drop_index(op.f('ix_workspaces_status'), table_name='workspaces')
    op.drop_index(op.f('ix_workspaces_user_id'), table_name='workspaces')
    op.drop_index(op.f('ix_workspaces_id'), table_name='workspaces')
    op.drop_table('workspaces')
    
    op.drop_index('ix_users_email_unique', table_name='users')
    op.drop_index(op.f('ix_users_is_deleted'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

