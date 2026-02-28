
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
DB_PATH = f"sqlite:///{db_root / 'ai_learning_table.db'}"

if os.getenv("CAREERTROJAN_DB_URL"):
    DB_PATH = os.getenv("CAREERTROJAN_DB_URL")

engine = create_engine(
    DB_PATH, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
