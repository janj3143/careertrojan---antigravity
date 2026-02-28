import argparse
import json
import sys
from typing import Iterable, Optional
from urllib import error, request


def _call(
    method: str,
    url: str,
    payload: Optional[dict] = None,
    expected_statuses: Iterable[int] = (200,),
    timeout: int = 15,
) -> bool:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            if status in expected_statuses:
                print(f"[PASS] {method} {url} -> {status}")
                return True
            print(f"[FAIL] {method} {url} -> {status} (expected {sorted(expected_statuses)})")
            return False
    except error.HTTPError as exc:
        status = exc.code
        if status in expected_statuses:
            print(f"[PASS] {method} {url} -> {status}")
            return True
        print(f"[FAIL] {method} {url} -> {status} (expected {sorted(expected_statuses)})")
        return False
    except Exception as exc:
        print(f"[FAIL] {method} {url} -> {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="CareerTrojan coaching endpoint uptime/shape checks")
    parser.add_argument("--base-url", default="http://127.0.0.1:8600", help="Backend base URL")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    checks = [
        ("GET", f"{base}/health", None, (200,)),
        ("POST", f"{base}/api/auth/v1/login", {}, (422,)),
        ("GET", f"{base}/api/coaching/v1/health", None, (200,)),
        (
            "POST",
            f"{base}/api/coaching/v1/questions/generate",
            {
                "question_type": "Marketing",
                "count": 5,
                "resume": {"work_experience": [{"title": "Marketing Executive"}]},
                "job": {"title": "Marketing Manager"},
                "fit": {"score": 0.73},
            },
            (200,),
        ),
        (
            "POST",
            f"{base}/api/coaching/v1/answers/review",
            {
                "question": "Tell me about a campaign you improved.",
                "answer": "I improved conversion by 18% by reworking landing page copy and segmentation.",
                "resume": {"skills": ["SEO", "campaign analytics"]},
                "job": {"title": "Growth Marketer"},
            },
            (200,),
        ),
        (
            "POST",
            f"{base}/api/coaching/v1/stories/generate",
            {
                "focus_areas": ["leadership", "problem-solving"],
                "resume": {"work_experience": [{"title": "Team Lead"}]},
                "job": {"title": "Operations Manager"},
            },
            (200,),
        ),
        ("GET", f"{base}/api/coaching/v1/learning/profile", None, (401, 403)),
    ]

    passed = 0
    for method, url, payload, statuses in checks:
        if _call(method, url, payload=payload, expected_statuses=statuses):
            passed += 1

    total = len(checks)
    print(f"\nSummary: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
