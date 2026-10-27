"""add deleted_at to scans

Revision ID: c3f1d89a4b22
Revises: b8c0b23862ee
Create Date: 2026-10-25 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3f1d89a4b22"
down_revision: Union[str, Sequence[str], None] = "b8c0b23862ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable deleted_at column to scans for soft-delete support."""
    op.add_column(
        "scans",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scans_deleted_at", "scans", ["deleted_at"])


def downgrade() -> None:
    """Remove deleted_at column from scans."""
    op.drop_index("ix_scans_deleted_at", table_name="scans")
    op.drop_column("scans", "deleted_at")
