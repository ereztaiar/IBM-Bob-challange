"""fix vector dimension to 768 for nomic-embed-text

Revision ID: a1b2c3d4e5f6
Revises: ed96e6207148
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "ed96e6207148"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Resize embedding columns from vector(1536) to vector(768).

    Existing rows are truncated to the new dimension via the USING clause.
    In practice the tables are empty on a fresh deployment; any pre-existing
    1536-dim vectors would be silently truncated, so run a re-seed after
    applying this migration if the knowledge base was already populated.
    """
    op.execute(
        "ALTER TABLE vulnerability_docs "
        "ALTER COLUMN embedding TYPE vector(768) "
        "USING embedding::text::vector(768)"
    )
    op.execute(
        "ALTER TABLE scan_embeddings "
        "ALTER COLUMN embedding TYPE vector(768) "
        "USING embedding::text::vector(768)"
    )


def downgrade() -> None:
    """Revert embedding columns back to vector(1536)."""
    op.execute(
        "ALTER TABLE vulnerability_docs "
        "ALTER COLUMN embedding TYPE vector(1536) "
        "USING embedding::text::vector(1536)"
    )
    op.execute(
        "ALTER TABLE scan_embeddings "
        "ALTER COLUMN embedding TYPE vector(1536) "
        "USING embedding::text::vector(1536)"
    )
