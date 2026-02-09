"""Admin API client additions for Token Economics.

Merge these methods into your existing services/admin_api_client.py (or equivalent).
Assumes you already have:
- self.get(path, params=...)
- base_url
- auth header injection

No fallbacks: callers enforce contracts.
"""

from typing import Any, Dict


class AdminAPIClientAdditions:
    """Mixin for services/admin_api_client.py.

    Add these methods to your canonical Admin API client so Page 10 (Token
    Management) can talk to the backend.
    """

    # ----------------------------
    # Token plans
    # ----------------------------

    def get_token_plans(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/plans")

    def update_token_plans(self, plans: Dict[str, Any]) -> Dict[str, Any]:
        return self.put("/admin/tokens/plans", json={"plans": plans})

    # ----------------------------
    # Token usage + subscriptions
    # ----------------------------

    def get_token_usage(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/usage")

    def get_user_subscriptions(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/subscriptions")

    # ----------------------------
    # Feature costs
    # ----------------------------

    def get_token_costs(self) -> Dict[str, Any]:
        return self.get("/admin/tokens/costs")

    def update_token_cost(self, feature: str, tokens: int) -> Dict[str, Any]:
        return self.put(f"/admin/tokens/costs/{feature}", json={"tokens": tokens})

    # ----------------------------
    # Logs + analytics
    # ----------------------------

    def get_usage_logs(self, days: int = 14) -> Dict[str, Any]:
        return self.get("/admin/tokens/logs", params={"days": days})

    def get_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        return self.get("/admin/tokens/analytics", params={"days": days})

    # ----------------------------
    # Ledgers
    # ----------------------------

    def get_user_token_ledger(self, user_id: str) -> Dict[str, Any]:
        return self.get(f"/admin/tokens/ledger/{user_id}")

    # ----------------------------
    # Health/contracts
    # ----------------------------

    def get_health(self) -> Dict[str, Any]:
        return self.get("/admin/health")

    # ----------------------------
    # Token economics (API-linked)
    # ----------------------------

    def get_token_economics_summary(self, window_days: int = 30, currency: str = "GBP") -> Dict[str, Any]:
        return self.get(
            "/admin/token-economics/summary",
            params={"window_days": window_days, "currency": currency},
        )
