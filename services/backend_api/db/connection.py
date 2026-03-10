
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from pathlib import Path

from services.shared.paths import CareerTrojanPaths

# Ensure DB directory exists
# Portable: env var or working-root fallback
_paths = CareerTrojanPaths()
db_root = Path(os.getenv("CAREERTROJAN_DB_DIR", str(_paths.working_root / "db")))
db_root.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{db_root / 'ai_learning_table.db'}"
DB_PATH = (
    os.getenv("CAREERTROJAN_DB_URL")
    or os.getenv("DATABASE_URL")
    or DEFAULT_SQLITE_URL
)

engine_kwargs = {}
if DB_PATH.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_PATH, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
