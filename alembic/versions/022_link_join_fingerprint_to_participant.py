"""Link join fingerprint records to participants

Revision ID: 022
Revises: 021
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_join_fingerprints",
        sa.Column("participant_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_session_join_fingerprints_participant_id",
        "session_join_fingerprints",
        "session_participants",
        ["participant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_session_join_fingerprints_participant_id",
        "session_join_fingerprints",
        ["participant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_session_join_fingerprints_participant_id",
        table_name="session_join_fingerprints",
    )
    op.drop_constraint(
        "fk_session_join_fingerprints_participant_id",
        "session_join_fingerprints",
        type_="foreignkey",
    )
    op.drop_column("session_join_fingerprints", "participant_id")

