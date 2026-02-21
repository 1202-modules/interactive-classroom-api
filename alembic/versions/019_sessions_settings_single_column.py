"""Replace custom_settings and template_snapshot with single settings column

Revision ID: 019
Revises: 018
Create Date: 2025-02-20

Session settings are now a full JSON copy (settings). Backfill from
template_snapshot/template + custom_settings, then drop old columns.
"""
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from utils.settings import merge_settings

    op.add_column(
        'sessions',
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )

    conn = op.get_bind()
    sessions = conn.execute(
        text('SELECT id, workspace_id, custom_settings, template_snapshot FROM sessions')
    ).fetchall()
    workspaces = {}
    for row in sessions:
        wid = row[1]
        if wid not in workspaces:
            w = conn.execute(
                text('SELECT template_settings FROM workspaces WHERE id = :id'),
                {'id': wid}
            ).fetchone()
            workspaces[wid] = (w[0] or {}) if w else {}
        template = workspaces[wid]
        base = row[3] if row[3] is not None else template
        custom = row[2] or {}
        if not isinstance(base, dict):
            base = {}
        if not isinstance(custom, dict):
            custom = {}
        merged = merge_settings(base, custom)
        # Pass as JSON string for PostgreSQL
        conn.execute(
            text('UPDATE sessions SET settings = CAST(:s AS json) WHERE id = :id'),
            {'s': json.dumps(merged) if merged else None, 'id': row[0]}
        )

    op.drop_column('sessions', 'custom_settings')
    op.drop_column('sessions', 'template_snapshot')


def downgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('template_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'sessions',
        sa.Column('custom_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(text("UPDATE sessions SET custom_settings = settings, template_snapshot = NULL WHERE settings IS NOT NULL"))
    op.drop_column('sessions', 'settings')
