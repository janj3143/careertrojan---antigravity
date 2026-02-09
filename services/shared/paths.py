"""
CareerTrojan — Cross-Platform Path Resolver
=============================================
Abstracts all drive-letter paths behind environment variables so the same
Python code runs on both Windows and Ubuntu without modification.

On Windows:  paths come from .env  (L:\..., E:\..., C:\...)
On Ubuntu:   paths come from careertrojan.env  (/mnt/careertrojan/..., /opt/careertrojan/...)

Usage:
    from services.shared.paths import paths
    data_root = paths.ai_data_final   # resolves to correct OS path
"""
import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger("careertrojan.paths")


@dataclass
class CareerTrojanPaths:
    """All canonical paths used by the runtime — resolved from env vars."""

    # ── Core Data ────────────────────────────────────────────
    data_root: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_DATA_ROOT",
        r"L:\VS ai_data final - version" if sys.platform == "win32" else "/mnt/careertrojan"
    )))

    ai_data_final: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_AI_DATA",
        r"L:\VS ai_data final - version\ai_data_final" if sys.platform == "win32" else "/mnt/careertrojan/ai_data_final"
    )))

    parser_root: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_PARSER_ROOT",
        r"L:\VS ai_data final - version\automated_parser" if sys.platform == "win32" else "/mnt/careertrojan/automated_parser"
    )))

    # ── User Data (primary + mirror) ─────────────────────────
    user_data: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_USER_DATA",
        r"L:\VS ai_data final - version\USER DATA" if sys.platform == "win32" else "/mnt/careertrojan/user_data"
    )))

    user_data_mirror: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_USER_DATA_MIRROR",
        r"E:\CareerTrojan\USER_DATA_COPY" if sys.platform == "win32" else "/mnt/careertrojan/backups/user_data"
    )))

    # ── Runtime ──────────────────────────────────────────────
    app_root: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_APP_ROOT",
        r"C:\careertrojan" if sys.platform == "win32" else "/opt/careertrojan/runtime"
    )))

    working_root: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_WORKING_ROOT",
        r"C:\careertrojan\working\working_copy" if sys.platform == "win32" else "/opt/careertrojan/runtime/working/working_copy"
    )))

    trained_models: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_MODELS",
        r"C:\careertrojan\trained_models" if sys.platform == "win32" else "/opt/careertrojan/runtime/trained_models"
    )))

    logs: Path = field(default_factory=lambda: Path(os.getenv(
        "CAREERTROJAN_APP_LOGS",
        r"C:\careertrojan\logs" if sys.platform == "win32" else "/mnt/careertrojan/logs"
    )))

    # ── User Data Subdirectories (derived) ───────────────────
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

    # ── Validation ───────────────────────────────────────────
    def validate(self, strict: bool = False) -> dict:
        """Check that all critical paths exist. Returns a report dict."""
        report = {}
        critical = ["data_root", "ai_data_final", "user_data"]
        recommended = ["parser_root", "user_data_mirror", "app_root"]

        for name in critical + recommended:
            p = getattr(self, name)
            exists = p.exists()
            report[name] = {"path": str(p), "exists": exists}
            if not exists and name in critical:
                msg = f"CRITICAL path missing: {name} = {p}"
                logger.error(msg)
                if strict:
                    raise FileNotFoundError(msg)
            elif not exists:
                logger.warning(f"Recommended path missing: {name} = {p}")

        return report

    def ensure_user_data_structure(self):
        """Create the canonical user data subdirectory tree in both primary and mirror."""
        subdirs = [
            "sessions", "profiles", "interactions", "cv_uploads",
            "ai_matches", "session_logs", "admin_2fa", "test_accounts",
            "trap_profiles", "trap_reports", "user_registry", "quarantine",
        ]
        for root in [self.user_data, self.user_data_mirror]:
            if root.exists() or root.parent.exists():
                for sub in subdirs:
                    (root / sub).mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensured user data structure at: {root}")

    @property
    def is_windows(self) -> bool:
        return sys.platform == "win32"

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


# ── Singleton ────────────────────────────────────────────────
paths = CareerTrojanPaths()
