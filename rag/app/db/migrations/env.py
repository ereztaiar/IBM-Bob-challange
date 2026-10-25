"""Alembic environment configuration for the RAG service.

Reads ``DATABASE_URL`` from the environment and converts the asyncpg URL to a
synchronous psycopg2 URL for Alembic's own migrations runner.  All models are
imported here so that ``autogenerate`` can detect schema changes.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Ensure the rag package is on sys.path when running from the rag/ dir
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

# ---------------------------------------------------------------------------
# Import Base and all models so autogenerate can discover them
# ---------------------------------------------------------------------------
from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: F401, E402  — registers all models on Base.metadata

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url() -> str:
    """Return a synchronous psycopg2 DATABASE_URL for Alembic.

    If the env var contains an asyncpg driver, it is swapped for psycopg2 so
    that Alembic's synchronous engine can connect.
    """
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url", ""))
    # Swap asyncpg driver for psycopg2 which Alembic's sync engine requires
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    # If no explicit driver is set, ensure psycopg2 is used
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection required)."""
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live DB connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_sync_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
