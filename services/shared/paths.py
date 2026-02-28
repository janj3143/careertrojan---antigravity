"""
CareerTrojan — Cross-Platform Path Resolver
============================================
Normalizes runtime paths so services can run whether `CAREERTROJAN_DATA_ROOT`
points to the data-root folder (containing `ai_data_final/`) or directly to
the `ai_data_final/` directory itself.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

logger = logging.getLogger("careertrojan.paths")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_windows() -> bool:
    return sys.platform == "win32"


def _expand(path_value: str | Path) -> Path:
    return Path(path_value).expanduser()


def _looks_like_ai_data_final(path: Path) -> bool:
    if path.name.casefold() == "ai_data_final":
        return True
    markers = ("parsed_resumes", "parsed_job_descriptions", "job_titles", "metadata")
    return path.exists() and path.is_dir() and any((path / marker).exists() for marker in markers)


def _normalize_data_root(path: Path) -> Path:
    expanded = _expand(path)
    if expanded.name.casefold() == "ai_data_final":
        return expanded.parent
    return expanded


def _default_data_root_candidates() -> List[Path]:
    project_root = _project_root()
    candidates: List[Path] = []
    if _is_windows():
        candidates.extend([
            Path(r"L:\Codec - Antigravity Data set"),
            Path(r"L:\Codec-Antigravity Data set"),
            Path(r"L:\VS ai_data final - version"),
            Path(r"L:\antigravity_version_ai_data_final"),
        ])
    else:
        candidates.extend([
            Path("/mnt/careertrojan"),
            Path("/mnt/ai-data"),
        ])
    candidates.extend([
        project_root / "data-mounts" / "ai-data",
        project_root / "data",
    ])
    return candidates


def _resolve_data_root() -> Path:
    env_root = os.getenv("CAREERTROJAN_DATA_ROOT")
    if env_root:
        return _normalize_data_root(Path(env_root))

    for candidate in _default_data_root_candidates():
        if not candidate.exists():
            continue
        if candidate.name.casefold() == "ai_data_final":
            return candidate.parent
        if (candidate / "ai_data_final").exists():
            return candidate
        if _looks_like_ai_data_final(candidate):
            return candidate.parent
        if (
            (candidate / "automated_parser").exists()
            or (candidate / "USER DATA").exists()
            or (candidate / "user_data").exists()
        ):
            return candidate

    # Deterministic fallback for first-run setups where folders may not exist yet.
    return _default_data_root_candidates()[0]


def _resolve_ai_data_final(data_root: Path) -> Path:
    env_ai_data = os.getenv("CAREERTROJAN_AI_DATA")
    if env_ai_data:
        return _expand(env_ai_data)

    if data_root.name.casefold() == "ai_data_final":
        return data_root

    candidate = data_root / "ai_data_final"
    if candidate.exists():
        return candidate

    if _looks_like_ai_data_final(data_root):
        return data_root

    return candidate


def _resolve_parser_root(data_root: Path) -> Path:
    env_parser = os.getenv("CAREERTROJAN_PARSER_ROOT")
    if env_parser:
        return _expand(env_parser)
    return data_root / "automated_parser"


def _resolve_user_data(data_root: Path) -> Path:
    env_user_data = os.getenv("CAREERTROJAN_USER_DATA")
    if env_user_data:
        return _expand(env_user_data)

    preferred = data_root / ("USER DATA" if _is_windows() else "user_data")
    alternate = data_root / ("user_data" if _is_windows() else "USER DATA")
    if preferred.exists() or not alternate.exists():
        return preferred
    return alternate


def _resolve_user_data_mirror() -> Path:
    env_mirror = os.getenv("CAREERTROJAN_USER_DATA_MIRROR")
    if env_mirror:
        return _expand(env_mirror)
    if _is_windows():
        return Path(r"E:\CareerTrojan\USER_DATA_COPY")
    return Path("/mnt/careertrojan/backups/user_data")


def _resolve_app_root() -> Path:
    env_app_root = os.getenv("CAREERTROJAN_APP_ROOT")
    if env_app_root:
        return _expand(env_app_root)
    return _project_root()


def _resolve_working_root(app_root: Path) -> Path:
    env_working = os.getenv("CAREERTROJAN_WORKING_ROOT")
    if env_working:
        return _expand(env_working)
    return app_root / "working" / "working_copy"


def _resolve_models_root(app_root: Path) -> Path:
    env_models = os.getenv("CAREERTROJAN_MODELS")
    if env_models:
        return _expand(env_models)
    return app_root / "trained_models"


def _resolve_logs_root(app_root: Path) -> Path:
    env_logs = os.getenv("CAREERTROJAN_APP_LOGS")
    if env_logs:
        return _expand(env_logs)
    return app_root / "logs"


@dataclass
class CareerTrojanPaths:
    """All canonical paths used by the runtime."""

    data_root: Path = field(default_factory=_resolve_data_root)
    ai_data_final: Path = field(init=False)
    parser_root: Path = field(init=False)
    user_data: Path = field(init=False)
    user_data_mirror: Path = field(init=False)
    app_root: Path = field(default_factory=_resolve_app_root)
    working_root: Path = field(init=False)
    trained_models: Path = field(init=False)
    logs: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_root = _normalize_data_root(self.data_root)
        self.ai_data_final = _resolve_ai_data_final(self.data_root)
        self.parser_root = _resolve_parser_root(self.data_root)
        self.user_data = _resolve_user_data(self.data_root)
        self.user_data_mirror = _resolve_user_data_mirror()
        self.app_root = _expand(self.app_root)
        self.working_root = _resolve_working_root(self.app_root)
        self.trained_models = _resolve_models_root(self.app_root)
        self.logs = _resolve_logs_root(self.app_root)

    @property
    def sessions(self) -> Path:
        return self.user_data / "sessions"

    @property
    def profiles(self) -> Path:
        return self.user_data / "profiles"

    @property
    def interactions(self) -> Path:
        return self.user_data / "interactions"

    @property
    def cv_uploads(self) -> Path:
        return self.user_data / "cv_uploads"

    @property
    def ai_matches(self) -> Path:
        return self.user_data / "ai_matches"

    @property
    def session_logs(self) -> Path:
        return self.user_data / "session_logs"

    @property
    def trap_profiles(self) -> Path:
        return self.user_data / "trap_profiles"

    @property
    def user_registry(self) -> Path:
        return self.user_data / "user_registry"

    def validate(self, strict: bool = False) -> dict:
        """Check that all critical paths exist. Returns a report dict."""
        report = {}
        critical = ["data_root", "ai_data_final", "user_data"]
        recommended = ["parser_root", "user_data_mirror", "app_root"]

        for name in critical + recommended:
            path_value = getattr(self, name)
            exists = path_value.exists()
            report[name] = {"path": str(path_value), "exists": exists}
            if not exists and name in critical:
                msg = f"CRITICAL path missing: {name} = {path_value}"
                logger.error(msg)
                if strict:
                    raise FileNotFoundError(msg)
            elif not exists:
                logger.warning("Recommended path missing: %s = %s", name, path_value)

        return report

    def ensure_user_data_structure(self) -> None:
        """Create the canonical user data subdirectory tree in primary and mirror."""
        subdirs = [
            "sessions",
            "profiles",
            "interactions",
            "cv_uploads",
            "ai_matches",
            "session_logs",
            "admin_2fa",
            "test_accounts",
            "trap_profiles",
            "trap_reports",
            "user_registry",
            "quarantine",
        ]
        for root in [self.user_data, self.user_data_mirror]:
            if root.exists() or root.parent.exists():
                for sub in subdirs:
                    (root / sub).mkdir(parents=True, exist_ok=True)
                logger.info("Ensured user data structure at: %s", root)

    @property
    def is_windows(self) -> bool:
        return _is_windows()

    @property
    def is_linux(self) -> bool:
        return sys.platform.startswith("linux")

    def summary(self) -> str:
        """Human-readable summary of all paths."""
        lines = [
            f"Platform: {'Windows' if self.is_windows else 'Linux'}",
            f"Data Root:      {self.data_root}",
            f"AI Data Final:  {self.ai_data_final}",
            f"Parser Root:    {self.parser_root}",
            f"User Data:      {self.user_data}",
            f"User Mirror:    {self.user_data_mirror}",
            f"App Root:       {self.app_root}",
            f"Models:         {self.trained_models}",
            f"Logs:           {self.logs}",
        ]
        return "\n".join(lines)


paths = CareerTrojanPaths()
