import os
from pathlib import Path


def load_env_file(filepath: Path) -> None:
    """Minimal .env loader to avoid python-dotenv dependency in this module."""
    path = Path(filepath).expanduser()
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


def _normalize_data_root(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.name.casefold() == "ai_data_final":
        return path.parent
    return path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load runtime environment from project-local locations first.
runtime_env_override = os.getenv("CAREERTROJAN_RUNTIME_ENV")
env_candidates = []
if runtime_env_override:
    env_candidates.append(Path(runtime_env_override))
env_candidates.extend([
    PROJECT_ROOT / "infra" / "env" / "runtime.env",
    PROJECT_ROOT / ".env",
])
for env_file in env_candidates:
    if env_file.exists():
        load_env_file(env_file)
        break

# Runtime Paths
runtime_root = Path(os.getenv("CAREERTROJAN_APP_ROOT", str(PROJECT_ROOT))).expanduser()
data_root = _normalize_data_root(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\Codec-Antigravity Data set"))
ai_data_override = os.getenv("CAREERTROJAN_AI_DATA")
if ai_data_override:
    AI_DATA_DIR = Path(ai_data_override).expanduser()
else:
    AI_DATA_DIR = data_root / "ai_data_final"
log_root = Path(
    os.getenv(
        "CAREERTROJAN_LOG_ROOT",
        os.getenv("CAREERTROJAN_APP_LOGS", str(runtime_root / "logs")),
    )
).expanduser()

# AI Engine Paths
ai_engine_root = runtime_root / "services" / "ai_engine"
models_path = ai_engine_root / "trained_models"

# Ensure directories exist
log_root.mkdir(parents=True, exist_ok=True)
models_path.mkdir(parents=True, exist_ok=True)

# Export for usage
RAW_DATA_DIR = data_root / "raw_data"
PROFILES_DIR = AI_DATA_DIR / "profiles"


def get_db_url():
    return os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/careertrojan")
