
import os
import sys
from pathlib import Path

# Manual .env parser to avoid python-dotenv dependency
def load_env_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Load runtime environment
env_path = Path(r"C:\careertrojan\infra\env\runtime.env")
load_env_file(env_path)

# Runtime Paths
runtime_root = Path(r"C:\careertrojan")
data_root = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
log_root = Path(os.getenv("CAREERTROJAN_LOG_ROOT", r"C:\careertrojan\logs"))

# AI Engine Paths
ai_engine_root = runtime_root / "services" / "ai_engine"
models_path = ai_engine_root / "trained_models"

# Ensure directories exist
log_root.mkdir(parents=True, exist_ok=True)
models_path.mkdir(parents=True, exist_ok=True)

# Export for usage
AI_DATA_DIR = data_root / "ai_data_final"
RAW_DATA_DIR = data_root / "raw_data"
PROFILES_DIR = AI_DATA_DIR / "profiles"

def get_db_url():
    return os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/careertrojan")
