from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


CORE_REQUIRED = [
    "PROJECT_NAME",
    "ENV",
    "DEBUG",
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "CAREERTROJAN_DATA_ROOT",
]

ZENDESK_REQUIRED = [
    "HELPDESK_PROVIDER",
    "ZENDESK_BASE_URL",
    "ZENDESK_EMAIL",
    "ZENDESK_API_TOKEN",
]


def _missing(env_map: dict[str, str], keys: list[str]) -> list[str]:
    missing = []
    for key in keys:
        value = (env_map.get(key) or "").strip()
        if not value:
            missing.append(key)
    return missing


def _warn_placeholder(key: str, value: str) -> bool:
    value_l = value.lower()
    patterns = [
        r"your-subdomain",
        r"replace",
        r"placeholder",
        r"change-in-production",
    ]
    return any(re.search(pattern, value_l) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate runtime environment variables")
    parser.add_argument("--env-file", default=".env", help="Path to env file")
    parser.add_argument("--strict", action="store_true", help="Fail on placeholder values")
    args = parser.parse_args()

    env_path = Path(args.env_file).resolve()
    if not env_path.exists():
        print(f"[FAIL] Env file not found: {env_path}")
        return 2

    env_map = parse_env_file(env_path)

    missing = _missing(env_map, CORE_REQUIRED)

    provider = (env_map.get("HELPDESK_PROVIDER") or "stub").strip().lower()
    if provider == "zendesk":
        missing.extend(_missing(env_map, ZENDESK_REQUIRED))

    if missing:
        print("[FAIL] Missing required environment keys:")
        for key in sorted(set(missing)):
            print(f"  - {key}")
        return 3

    if args.strict:
        strict_keys = CORE_REQUIRED + ZENDESK_REQUIRED
        offenders = []
        for key in strict_keys:
            value = (env_map.get(key) or "").strip()
            if value and _warn_placeholder(key, value):
                offenders.append(key)
        if offenders:
            print("[FAIL] Placeholder-like values found in strict mode:")
            for key in offenders:
                print(f"  - {key}")
            return 4

    print(f"[OK] Runtime environment valid: {env_path}")
    print(f"[INFO] Helpdesk provider: {provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
