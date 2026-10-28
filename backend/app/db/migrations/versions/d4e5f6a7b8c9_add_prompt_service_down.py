"""add prompt_service_down to scans

Revision ID: d4e5f6a7b8c9
Revises: c3f1d89a4b22
Create Date: 2026-10-26 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3f1d89a4b22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add prompt_service_down boolean column to scans (defaults to false)."""
    op.add_column(
        "scans",
        sa.Column(
            "prompt_service_down",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Remove prompt_service_down column from scans."""
    op.drop_column("scans", "prompt_service_down")
