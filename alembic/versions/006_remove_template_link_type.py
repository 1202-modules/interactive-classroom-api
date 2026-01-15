"""Remove template_link_type from sessions

Revision ID: 006_remove_template_link_type
Revises: 005_add_session_settings_template
Create Date: 2025-01-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Drop template_link_type column from sessions table
    op.drop_column('sessions', 'template_link_type')


def downgrade():
    # Re-add template_link_type column
    op.add_column('sessions', sa.Column('template_link_type', sa.String(), nullable=False, server_default='full'))

