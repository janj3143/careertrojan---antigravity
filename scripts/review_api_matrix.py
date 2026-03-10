#!/usr/bin/env python3
"""
Review Pack 1: API Regression Matrix
Runs a deterministic endpoint matrix against a running CareerTrojan stack.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Iterable

import requests


@dataclass
class EndpointCase:
    name: str
    method: str
    path: str
    expected_statuses: tuple[int, ...]
    json_body: dict | None = None


def _run_case(base_url: str, case: EndpointCase, timeout: int) -> tuple[bool, dict]:
    url = f"{base_url}{case.path}"
    method = case.method.upper()

    if method == "GET":
        resp = requests.get(url, timeout=timeout)
    elif method == "POST":
        resp = requests.post(url, json=case.json_body or {}, timeout=timeout)
    else:
        raise ValueError(f"Unsupported method: {method}")

    ok = resp.status_code in case.expected_statuses
    payload = {
        "name": case.name,
        "method": method,
        "path": case.path,
        "status": resp.status_code,
        "expected": list(case.expected_statuses),
        "ok": ok,
        "preview": (resp.text or "")[:240],
    }
    return ok, payload


def _print_line(ok: bool, name: str, status: int, expected: Iterable[int]) -> None:
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name} -> {status} (expected: {list(expected)})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CareerTrojan API regression matrix")
    parser.add_argument("--base-url", default="http://localhost:8600", help="API base URL")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout in seconds")
    parser.add_argument(
        "--out",
        default="reports/review_api_matrix.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    cases = [
        EndpointCase("Liveness", "GET", "/health/live", (200,)),
        EndpointCase("Readiness", "GET", "/health/ready", (200,)),
        EndpointCase("OpenAPI", "GET", "/openapi.json", (200,)),
        EndpointCase("Ops Public Stats", "GET", "/api/ops/v1/stats/public", (200,)),
        EndpointCase("Intelligence Market", "GET", "/api/intelligence/v1/market", (200,)),
        EndpointCase(
            "Ops Processing Start",
            "POST",
            "/api/ops/v1/processing/start",
            (200,),
            {"pdfs": True, "full_scan": False, "trigger_enrichment": True},
        ),
        EndpointCase(
            "Lenses Spider",
            "POST",
            "/api/lenses/v1/spider",
            (200,),
            {
                "user_id": "review_user",
                "resume_id": "RES_REVIEW",
                "job_family": "Software Engineering",
                "cohort": {"id": "CH_REVIEW"},
            },
        ),
        EndpointCase("Mentor Dashboard", "GET", "/api/mentor/v1/mentor_e2e_99/dashboard-stats", (200,)),
        EndpointCase("Payment Health", "GET", "/api/payment/v1/health", (200,)),
        EndpointCase("Payment Client Token", "GET", "/api/payment/v1/client-token", (200, 401, 403)),
        EndpointCase("Mentor Package Lookup", "GET", "/api/mentor/v1/ment_99/packages/pkg_mock", (404,)),
    ]

    print("=== CareerTrojan Review API Matrix ===")
    print(f"Base URL: {args.base_url}")

    results = []
    passed = 0

    for case in cases:
        try:
            ok, payload = _run_case(args.base_url, case, args.timeout)
        except Exception as exc:  # pragma: no cover
            ok = False
            payload = {
                "name": case.name,
                "method": case.method,
                "path": case.path,
                "status": None,
                "expected": list(case.expected_statuses),
                "ok": False,
                "preview": str(exc),
            }
        _print_line(ok, payload["name"], payload["status"], payload["expected"])
        results.append(payload)
        passed += int(ok)

    summary = {
        "base_url": args.base_url,
        "passed": passed,
        "failed": len(cases) - passed,
        "total": len(cases),
        "results": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary: {passed}/{len(cases)} passed")
    print(f"Report: {args.out}")

    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
