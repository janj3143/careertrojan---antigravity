"""
Alembic env.py — CareerTrojan database migrations
===================================================

Reads the DB URL from the same environment variables as the application
(CAREERTROJAN_DB_URL → DATABASE_URL → SQLite fallback) so migrations
always target the correct database.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to sys.path so "services.*" imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import all SQLAlchemy models so Alembic's autogenerate sees them
from services.backend_api.db.models import Base  # noqa: E402

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Resolve database URL — same priority as services/backend_api/db/connection.py
# ---------------------------------------------------------------------------
_data_root = os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
_sqlite_fallback = f"sqlite:///{_data_root}/ai_learning_table.db"

DATABASE_URL = (
    os.getenv("CAREERTROJAN_DB_URL")
    or os.getenv("DATABASE_URL")
    or _sqlite_fallback
)

# Override whatever alembic.ini has with the resolved env URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
