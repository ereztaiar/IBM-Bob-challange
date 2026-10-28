"""Admin model — admin accounts that can access the admin dashboard."""

from __future__ import annotations

import uuid

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Admin(Base):
    """Represents an admin user who can log in to the admin dashboard.

    Passwords are stored as bcrypt hashes and never in plain text.
    This table is seeded at startup from the ``ADMIN_USERNAME`` /
    ``ADMIN_PASSWORD`` environment variables.
    """

    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
