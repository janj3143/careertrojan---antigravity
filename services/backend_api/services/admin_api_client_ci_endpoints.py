"""services.admin_api_client – Competitive Intelligence endpoints (PATCH)

Copy these methods into your existing AdminFastAPIClient (or the class
returned by get_admin_api_client) so Page 11 can call them.

Assumptions:
- Your client already has a low-level request helper such as:
    self._get(path, params=None)
    self._post(path, json=None)
    self._put(path, json=None)
    self._delete(path)
- Paths are under /admin/competitive-intel (recommended), but adjust to match your backend.

Backend contract is strict: the page will raise if expected keys are missing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class CompetitiveIntelAdminClientMixin:
    """Mixin you can add to your Admin client class."""

    # -----------------------------
    # Overview
    # -----------------------------
    def get_ci_overview(self) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/overview")

    # -----------------------------
    # Competitors (CRUD)
    # -----------------------------
    def get_ci_competitors(self) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/competitors")

    def upsert_ci_competitor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload should include id (optional), name, website, tags, notes, monitored (bool)
        return self._post("/admin/competitive-intel/competitors", json=payload)

    def delete_ci_competitor(self, competitor_id: str) -> Dict[str, Any]:
        return self._delete(f"/admin/competitive-intel/competitors/{competitor_id}")

    # -----------------------------
    # Signals / Trends
    # -----------------------------
    def get_ci_signals(self, days: int = 30) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/signals", params={"days": int(days)})

    # -----------------------------
    # Benchmarks
    # -----------------------------
    def get_ci_benchmarks(self) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/benchmarks")

    # -----------------------------
    # Tasks
    # -----------------------------
    def get_ci_tasks(self) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/tasks")

    def create_ci_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload: {name, kind, schedule?, params?}
        return self._post("/admin/competitive-intel/tasks", json=payload)

    def run_ci_task(self, task_id: str) -> Dict[str, Any]:
        return self._post(f"/admin/competitive-intel/tasks/{task_id}/run")

    def delete_ci_task(self, task_id: str) -> Dict[str, Any]:
        return self._delete(f"/admin/competitive-intel/tasks/{task_id}")

    # -----------------------------
    # Reports
    # -----------------------------
    def get_ci_reports(self, days: int = 30) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/reports", params={"days": int(days)})

    def get_ci_report(self, report_id: str) -> Dict[str, Any]:
        return self._get(f"/admin/competitive-intel/reports/{report_id}")

    # -----------------------------
    # Config
    # -----------------------------
    def get_ci_config(self) -> Dict[str, Any]:
        return self._get("/admin/competitive-intel/config")

    def update_ci_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._put("/admin/competitive-intel/config", json=payload)
