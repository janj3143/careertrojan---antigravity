
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# ---------------------------------------------------------------------------
# Resolve database URL
# Priority: CAREERTROJAN_DB_URL > DATABASE_URL > local SQLite fallback
# Docker compose sets DATABASE_URL; local dev may set CAREERTROJAN_DB_URL.
# ---------------------------------------------------------------------------
DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
_sqlite_fallback = f"sqlite:///{DATA_ROOT}/ai_learning_table.db"

DATABASE_URL: str = (
    os.getenv("CAREERTROJAN_DB_URL")
    or os.getenv("DATABASE_URL")
    or _sqlite_fallback
)

# check_same_thread is only valid for SQLite
_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
