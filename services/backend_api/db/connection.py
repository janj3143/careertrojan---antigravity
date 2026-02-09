
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Ensure DB directory exists
# Portable: env var or local fallback
DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
DB_PATH = f"sqlite:///{DATA_ROOT}/ai_learning_table.db"

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
