#!/usr/bin/env python3
"""
Review Pack 2: New Elements Validation
Checks middleware/contract elements that are easy to regress during refactors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate new review elements")
    parser.add_argument("--base-url", default="http://localhost:8600")
    parser.add_argument("--out", default="reports/review_new_elements.json")
    args = parser.parse_args()

    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}")

    # 1) Request correlation header presence
    r = requests.get(f"{args.base_url}/health/live", timeout=20)
    req_id = r.headers.get("x-request-id") or r.headers.get("X-Request-ID")
    add("Request Correlation Header", bool(req_id), f"x-request-id={req_id}")

    # 2) OpenAPI includes key rewired endpoints
    r = requests.get(f"{args.base_url}/openapi.json", timeout=20)
    openapi = r.json()
    paths = set(openapi.get("paths", {}).keys())
    required_paths = {
        "/api/lenses/v1/spider",
        "/api/ops/v1/processing/start",
        "/api/payment/v1/health",
    }
    missing = sorted(required_paths - paths)
    add("OpenAPI Rewired Paths", len(missing) == 0, f"missing={missing}")

    # 3) No NotImplemented/501 leakage in responses for critical paths
    probe_paths = [
        "/api/intelligence/v1/market",
        "/api/lenses/v1/spider",
        "/api/ops/v1/stats/public",
    ]
    leak_hits = []

    for p in probe_paths:
        if p.endswith("/spider"):
            rr = requests.post(
                f"{args.base_url}{p}",
                json={
                    "user_id": "review_user",
                    "resume_id": "RES_REVIEW",
                    "job_family": "Software Engineering",
                    "cohort": {"id": "CH_REVIEW"},
                },
                timeout=20,
            )
        else:
            rr = requests.get(f"{args.base_url}{p}", timeout=20)
        body = rr.text or ""
        if rr.status_code == 501 or re.search(r"NotImplemented|not implemented|stub", body, flags=re.I):
            leak_hits.append({"path": p, "status": rr.status_code})

    add("No Maths-Theatre Leakage", len(leak_hits) == 0, f"hits={leak_hits}")

    # 4) Billing path correctness check
    ok_payment = requests.get(f"{args.base_url}/api/payment/v1/health", timeout=20).status_code == 200
    wrong_path = requests.get(f"{args.base_url}/api/v1/payment/health", timeout=20).status_code
    add("Billing Route Contract", ok_payment and wrong_path == 404, f"correct=200 wrong_path={wrong_path}")

    passed = sum(1 for c in checks if c["ok"])
    result = {
        "base_url": args.base_url,
        "passed": passed,
        "failed": len(checks) - passed,
        "checks": checks,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nSummary: {passed}/{len(checks)} passed")
    print(f"Report: {args.out}")

    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
