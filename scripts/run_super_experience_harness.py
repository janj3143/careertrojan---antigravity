from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backend_api.main import app  # noqa: E402
from services.backend_api.db.connection import SessionLocal  # noqa: E402
from services.backend_api.db import models  # noqa: E402


@dataclass
class StepResult:
    name: str
    ok: bool
    status_code: Optional[int] = None
    detail: str = ""
    payload_preview: Optional[Dict[str, Any]] = None


@dataclass
class RoleJourney:
    role: str
    steps: List[StepResult]


@dataclass
class HarnessReport:
    started_at: str
    finished_at: Optional[str]
    tiers: Dict[str, Any]
    role_journeys: List[RoleJourney]
    ai_learning_signals: Dict[str, Any]
    expected_gaps: List[str]
    resume_probe: Dict[str, Any]


class SuperHarness:
    def __init__(self, run_tiers: bool, resume_path: Optional[str], output_path: Path) -> None:
        self.run_tiers = run_tiers
        self.resume_path = resume_path
        self.output_path = output_path
        self.client = TestClient(app, raise_server_exceptions=False)
        self.expected_gaps: List[str] = []

    def _result(self, name: str, response=None, *, ok: bool = True, detail: str = "") -> StepResult:
        preview = None
        status_code = None
        if response is not None:
            status_code = response.status_code
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    preview = {k: payload[k] for k in list(payload.keys())[:8]}
            except Exception:
                preview = None
        return StepResult(name=name, ok=ok, status_code=status_code, detail=detail, payload_preview=preview)

    def _run_pytest_tier(self, name: str, args: List[str]) -> Dict[str, Any]:
        cmd = [sys.executable, "-m", "pytest", *args]
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
        )
        return {
            "name": name,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "command": " ".join(cmd),
            "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]),
        }

    def run_tiered_tests(self) -> Dict[str, Any]:
        if not self.run_tiers:
            return {"skipped": True}

        unit = self._run_pytest_tier("unit", ["tests/unit", "-q", "--tb=short", "--no-header"])
        integration = self._run_pytest_tier("integration", ["tests/integration", "-q", "--tb=short", "--no-header"])
        e2e = self._run_pytest_tier("e2e", ["tests/e2e", "-q", "--tb=short", "--no-header"])
        return {"skipped": False, "unit": unit, "integration": integration, "e2e": e2e}

    def _register_and_login(self, email: str, password: str, *, full_name: str) -> str:
        self.client.post(
            "/api/auth/v1/register",
            params={"email": email, "password": password, "full_name": full_name},
        )
        login = self.client.post(
            "/api/auth/v1/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login.json().get("access_token") if login.status_code == 200 else None
        if not token:
            raise RuntimeError(f"Unable to login {email}: {login.status_code} {login.text}")
        return token

    def _upsert_role(self, email: str, role: str) -> Optional[models.User]:
        db = SessionLocal()
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if not user:
                return None
            user.role = role
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    def _ensure_mentor_profile(self, user: models.User) -> Optional[models.Mentor]:
        db = SessionLocal()
        try:
            mentor = db.query(models.Mentor).filter(models.Mentor.user_id == user.id).first()
            if mentor:
                return mentor
            mentor = models.Mentor(user_id=user.id, specialty="career", hourly_rate=120.0, availability="available")
            db.add(mentor)
            db.commit()
            db.refresh(mentor)
            return mentor
        finally:
            db.close()

    def user_journey(self, token: str) -> RoleJourney:
        headers = {"Authorization": f"Bearer {token}"}
        steps: List[StepResult] = []

        me = self.client.get("/api/user/v1/me", headers=headers)
        steps.append(self._result("user.me", me, ok=me.status_code == 200))

        profile = self.client.put(
            "/api/user/v1/profile",
            params={"bio": "Harness user", "location": "London"},
            headers=headers,
        )
        steps.append(self._result("user.profile.update", profile, ok=profile.status_code == 200))

        stats = self.client.get("/api/user/v1/stats", headers=headers)
        steps.append(self._result("user.stats", stats, ok=stats.status_code == 200))

        support_status = self.client.get("/api/support/v1/status")
        steps.append(self._result("support.status", support_status, ok=support_status.status_code == 200))

        support_readiness = self.client.get("/api/support/v1/readiness")
        steps.append(self._result("support.readiness", support_readiness, ok=support_readiness.status_code == 200))

        return RoleJourney(role="user", steps=steps)

    def admin_journey(self, token: str) -> RoleJourney:
        headers = {"Authorization": f"Bearer {token}"}
        steps: List[StepResult] = []

        sys_health = self.client.get("/api/admin/v1/system/health", headers=headers)
        steps.append(self._result("admin.system.health", sys_health, ok=sys_health.status_code == 200))

        integrations = self.client.get("/api/admin/v1/integrations/status", headers=headers)
        steps.append(self._result("admin.integrations.status", integrations, ok=integrations.status_code == 200))

        compliance = self.client.get("/api/admin/v1/compliance/summary", headers=headers)
        steps.append(self._result("admin.compliance.summary", compliance, ok=compliance.status_code == 200))

        return RoleJourney(role="admin", steps=steps)

    def mentor_journey(self, token: str, mentor_user_id: int, mentor_profile_id: int) -> RoleJourney:
        headers = {"Authorization": f"Bearer {token}"}
        steps: List[StepResult] = []

        by_user = self.client.get(f"/api/mentor/v1/profile-by-user/{mentor_user_id}", headers=headers)
        steps.append(self._result("mentor.profile.by_user", by_user, ok=by_user.status_code == 200))

        profile = self.client.get(f"/api/mentor/v1/{mentor_profile_id}/profile", headers=headers)
        steps.append(self._result("mentor.profile", profile, ok=profile.status_code == 200))

        packages = self.client.get(f"/api/mentor/v1/{mentor_profile_id}/packages", headers=headers)
        ok_packages = packages.status_code in (200, 501)
        steps.append(self._result("mentor.packages", packages, ok=ok_packages))
        if packages.status_code == 501:
            self.expected_gaps.append("Mentor packages endpoints return 501 (not configured)")

        dashboard = self.client.get(f"/api/mentor/v1/{mentor_profile_id}/dashboard-stats", headers=headers)
        ok_dash = dashboard.status_code in (200, 501)
        steps.append(self._result("mentor.dashboard", dashboard, ok=ok_dash))
        if dashboard.status_code == 501:
            self.expected_gaps.append("Mentor dashboard stats endpoint returns 501 (not configured)")

        return RoleJourney(role="mentor", steps=steps)

    def ai_learning_signals(self) -> Dict[str, Any]:
        queue_stats = self.client.get("/api/support/v1/ai/queue-stats")
        jobs = self.client.get("/api/support/v1/ai/jobs", params={"bucket": "processed", "limit": 10})

        return {
            "queue_stats_status": queue_stats.status_code,
            "queue_stats": queue_stats.json() if queue_stats.status_code == 200 else {"error": queue_stats.text},
            "processed_jobs_status": jobs.status_code,
            "processed_jobs": jobs.json() if jobs.status_code == 200 else {"error": jobs.text},
        }

    def resume_probe(self) -> Dict[str, Any]:
        if not self.resume_path:
            return {
                "status": "skipped",
                "reason": "No --resume-path provided",
            }

        path = Path(self.resume_path)
        if not path.exists():
            return {
                "status": "error",
                "reason": f"Resume file not found: {path}",
            }

        return {
            "status": "ready",
            "path": str(path),
            "message": "Resume provided. Upload/ingestion live-run step can be executed next with user token.",
        }

    def run(self) -> HarnessReport:
        started = datetime.now(timezone.utc).isoformat()
        tiers = self.run_tiered_tests()

        user_token = self._register_and_login("harness_user@careertrojan.local", "HarnessPass!123", full_name="Harness User")
        admin_token = self._register_and_login("harness_admin@careertrojan.local", "HarnessPass!123", full_name="Harness Admin")
        mentor_token = self._register_and_login("harness_mentor@careertrojan.local", "HarnessPass!123", full_name="Harness Mentor")

        admin_user = self._upsert_role("harness_admin@careertrojan.local", "admin")
        mentor_user = self._upsert_role("harness_mentor@careertrojan.local", "mentor")
        if not admin_user or not mentor_user:
            raise RuntimeError("Failed to set harness roles")

        mentor_profile = self._ensure_mentor_profile(mentor_user)
        if not mentor_profile:
            raise RuntimeError("Failed to ensure mentor profile")

        # refresh tokens with updated roles
        admin_token = self._register_and_login("harness_admin@careertrojan.local", "HarnessPass!123", full_name="Harness Admin")
        mentor_token = self._register_and_login("harness_mentor@careertrojan.local", "HarnessPass!123", full_name="Harness Mentor")

        journeys = [
            self.user_journey(user_token),
            self.admin_journey(admin_token),
            self.mentor_journey(mentor_token, mentor_user.id, mentor_profile.id),
        ]

        report = HarnessReport(
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
            tiers=tiers,
            role_journeys=journeys,
            ai_learning_signals=self.ai_learning_signals(),
            expected_gaps=sorted(set(self.expected_gaps)),
            resume_probe=self.resume_probe(),
        )

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(asdict(report), indent=2, default=str), encoding="utf-8")
        return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CareerTrojan Super Comprehensive Test Harness")
    parser.add_argument(
        "--run-tiers",
        action="store_true",
        help="Run unit/integration/e2e pytest tiers before role journeys.",
    )
    parser.add_argument(
        "--resume-path",
        type=str,
        default="",
        help="Optional resume path to stage for follow-up live user run.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "logs" / "test_results" / "super_harness_report.json"),
        help="Output JSON report path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    harness = SuperHarness(
        run_tiers=args.run_tiers,
        resume_path=args.resume_path or None,
        output_path=Path(args.output),
    )
    report = harness.run()

    journey_ok = all(all(step.ok for step in journey.steps) for journey in report.role_journeys)
    tiers_ok = report.tiers.get("skipped") or (
        report.tiers["unit"]["ok"] and report.tiers["integration"]["ok"] and report.tiers["e2e"]["ok"]
    )

    print(f"[HARNESS] Report written to: {harness.output_path}")
    print(f"[HARNESS] Journeys ok: {journey_ok}")
    print(f"[HARNESS] Tiers ok: {tiers_ok}")
    if report.expected_gaps:
        print("[HARNESS] Expected gaps:")
        for gap in report.expected_gaps:
            print(f"  - {gap}")

    return 0 if journey_ok and tiers_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
