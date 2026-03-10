from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RUNTIME_PATHS = [
    "services/backend_api",
    "services/shared/portal-bridge",
    "config/nginx",
]

BANNED_PATTERNS = [
    r"\bmock\b",
    r"\bdemo\b",
    r"\bplaceholder\b",
    r"\bfake\b",
    r"\bdummy\b",
    r"\bstub\b",
    r"\bexample_output\b",
]

ALLOW_PATTERNS = [
    r"\brandom\.sample\s*\(",
]


class Offender:
    def __init__(self, file_path: str, line_no: int, pattern: str, line: str) -> None:
        self.file_path = file_path
        self.line_no = line_no
        self.pattern = pattern
        self.line = line


def _run_git_diff(base_ref: Optional[str], head_ref: Optional[str], paths: Iterable[str]) -> str:
    cmd: List[str] = ["git", "diff", "--unified=0", "--no-color"]
    if base_ref and head_ref:
        cmd.append(f"{base_ref}..{head_ref}")
    cmd.extend(list(paths))

    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode == 0:
        return result.stdout

    fallback_cmd = ["git", "diff", "--unified=0", "--no-color", "HEAD~1..HEAD"]
    fallback_cmd.extend(list(paths))
    fallback = subprocess.run(
        fallback_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if fallback.returncode == 0:
        return fallback.stdout

    local_cmd = ["git", "diff", "--unified=0", "--no-color"]
    local_cmd.extend(list(paths))
    local = subprocess.run(
        local_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if local.returncode == 0:
        return local.stdout

    print("[FAIL] Unable to read git diff for banned-token validation")
    print(result.stderr.strip())
    return ""


def _is_allowed(line: str, allow_compiled: List[re.Pattern[str]]) -> bool:
    return any(pattern.search(line) for pattern in allow_compiled)


def _scan_added_lines(diff_text: str) -> list[Offender]:
    offenders: list[Offender] = []
    banned_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in BANNED_PATTERNS]
    allow_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in ALLOW_PATTERNS]

    current_file = ""
    current_line_no = 0

    for raw in diff_text.splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            continue

        if raw.startswith("@@"):
            # Hunk header format: @@ -old,+new @@
            m = re.search(r"\+(\d+)", raw)
            if m:
                current_line_no = int(m.group(1))
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            line = raw[1:]
            if _is_allowed(line, allow_compiled):
                current_line_no += 1
                continue
            for pattern in banned_compiled:
                if pattern.search(line):
                    offenders.append(
                        Offender(
                            file_path=current_file,
                            line_no=current_line_no,
                            pattern=pattern.pattern,
                            line=line.strip(),
                        )
                    )
                    break
            current_line_no += 1
            continue

        if raw.startswith(" "):
            current_line_no += 1

    return offenders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when banned non-live tokens are introduced in runtime code changes"
    )
    parser.add_argument("--base-ref", default="", help="Optional git base ref/sha")
    parser.add_argument("--head-ref", default="", help="Optional git head ref/sha")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=DEFAULT_RUNTIME_PATHS,
        help="Runtime paths to scan",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_ref = args.base_ref.strip() or None
    head_ref = args.head_ref.strip() or None

    diff_text = _run_git_diff(base_ref=base_ref, head_ref=head_ref, paths=args.paths)

    if not diff_text.strip():
        print("[OK] No runtime diff content to scan for banned tokens.")
        return 0

    offenders = _scan_added_lines(diff_text)

    if offenders:
        print("RUNTIME_BANNED_TOKEN_GATE_FAIL")
        for offender in offenders:
            print(
                f"- {offender.file_path}:{offender.line_no} matched {offender.pattern} :: {offender.line}"
            )
        return 1

    print("RUNTIME_BANNED_TOKEN_GATE_OK")
    print(f"- scanned paths: {', '.join(args.paths)}")
    print("- no banned tokens introduced in added runtime lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
