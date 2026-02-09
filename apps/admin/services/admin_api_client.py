from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class AdminFastAPIClient:
    """Thin HTTP client for admin endpoints (backend is single source of truth).

    Contract rules:
    - Never synthesize data.
    - HTTP errors bubble up with clear context.
    """

    base_url: str
    access_token: str
    timeout_s: int = 30

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _raise(self, r: requests.Response) -> None:
        if r.ok:
            return
        try:
            body = r.json()
        except Exception:
            body = r.text
        raise RuntimeError(f"Admin API error {r.status_code} {r.request.method} {r.url}: {body}")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.get(self._url(path), headers=self._headers(), params=params, timeout=self.timeout_s)
        self._raise(r)
        return r.json()

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.post(self._url(path), headers=self._headers(), json=json or {}, timeout=self.timeout_s)
        self._raise(r)
        return r.json()

    # -------------------------
    # Token Management endpoints
    # -------------------------
    def get_token_plans(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/plans")

    def update_token_plans(self, plans: Dict[str, Any]) -> Dict[str, Any]:
        return self.post("/admin/tokens/plans", json={"plans": plans})

    def get_token_usage(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/usage")

    def get_user_subscriptions(self) -> Dict[str, Any]:
        return self.get("/admin/subscriptions")

    def get_token_costs(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/costs")

    def update_token_cost(self, feature: str, tokens: int) -> Dict[str, Any]:
        return self.post("/admin/tokens/costs/update", json={"feature": feature, "tokens": tokens})

    def get_usage_logs(self, days: int = 14) -> Dict[str, Any]:
        return self.get("/admin/tokens/logs", params={"days": days})

    def get_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        return self.get("/admin/tokens/analytics", params={"days": days})

    def get_user_token_ledger(self, user_id: str) -> Dict[str, Any]:
        return self.get(f"/admin/tokens/ledger/{user_id}")

    def get_health(self) -> Dict[str, Any]:
        return self.get("/health")

    # -----------------------------------
    # Web Company Intelligence endpoints
    # -----------------------------------
    def webintel_company_index(self, q: str = "", limit: int = 100) -> Dict[str, Any]:
        return self.get("/admin/webintel/companies", params={"q": q, "limit": limit})

    def webintel_industry_index(self, q: str = "", limit: int = 200) -> Dict[str, Any]:
        return self.get("/admin/webintel/industries", params={"q": q, "limit": limit})

    def webintel_research_company(
        self,
        company_name: str,
        depth: str = "standard",
        include_news: bool = True,
        include_tech_stack: bool = True,
    ) -> Dict[str, Any]:
        return self.post(
            "/admin/webintel/research/company",
            json={
                "company_name": company_name,
                "depth": depth,
                "include_news": include_news,
                "include_tech_stack": include_tech_stack,
            },
        )

    def webintel_analyze_industry(
        self,
        industry: str,
        include_trends: bool = True,
        include_funding: bool = False,
        include_talent: bool = False,
    ) -> Dict[str, Any]:
        return self.post(
            "/admin/webintel/analyze/industry",
            json={
                "industry": industry,
                "include_trends": include_trends,
                "include_funding": include_funding,
                "include_talent": include_talent,
            },
        )

    def webintel_competitive_compare(
        self,
        primary_company: str,
        competitors: list[str],
        criteria: list[str],
    ) -> Dict[str, Any]:
        return self.post(
            "/admin/webintel/analyze/competitive",
            json={
                "primary_company": primary_company,
                "competitors": competitors,
                "criteria": criteria,
            },
        )

    def webintel_bulk_research(
        self,
        companies: list[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.post(
            "/admin/webintel/research/bulk",
            json={
                "companies": companies,
                "options": options,
            },
        )

    def webintel_integrations_status(self) -> Dict[str, Any]:
        return self.get("/admin/webintel/integrations")

    def webintel_list_reports(self, limit: int = 50) -> Dict[str, Any]:
        return self.get("/admin/webintel/reports", params={"limit": limit})

    def webintel_save_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        return self.post("/admin/webintel/reports/save", json={"report": report})


def get_admin_api_client(access_token: str) -> AdminFastAPIClient:
    base_url = os.getenv("ADMIN_API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
    timeout_s = int(os.getenv("ADMIN_API_TIMEOUT_S") or "30")
    return AdminFastAPIClient(base_url=base_url, access_token=access_token, timeout_s=timeout_s)