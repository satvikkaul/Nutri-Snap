# backend/migrations/env.py
from pathlib import Path
import sys, os
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# add PROJECT ROOT to sys.path
ROOT = Path(__file__).resolve().parents[2]   # …/Nutri-Snap
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()
config = context.config
cfg = config.get_section(config.config_ini_section) or {}
cfg["sqlalchemy.url"] = os.getenv("DATABASE_URL") or "sqlite:///./nutrisnap.db"

from backend.db import Base            # package import
import backend.models  # noqa: F401     # ensure metadata is loaded

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=cfg["sqlalchemy.url"], target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
