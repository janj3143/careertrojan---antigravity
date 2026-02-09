from __future__ import annotations

import os
from pathlib import Path

# Centralized IntelliCV paths.
# Override via environment variables to support local / docker / prod.

def _p(env_key: str, default: str) -> Path:
    return Path(os.getenv(env_key, default)).expanduser()

# Core datasets
AI_DATA_DIR: Path = _p("AI_DATA_DIR", "C:/IntelliCV-AI/IntelliCV/SANDBOX/ai_data_final")
RAW_DATA_DIR: Path = _p("RAW_DATA_DIR", "C:/IntelliCV-AI/IntelliCV/SANDBOX/raw_data")
USER_DATA_DIR: Path = _p("USER_DATA_DIR", "C:/IntelliCV-AI/IntelliCV/SANDBOX/user_data")

# Convenience
GENERATED_CONTENT_DIR: Path = _p("GENERATED_CONTENT_DIR", "C:/IntelliCV/generated_content")

