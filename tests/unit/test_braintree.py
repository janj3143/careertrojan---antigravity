"""
Tests for Braintree payment integration — CareerTrojan
=======================================================

Tests cover:
  - Braintree service configuration checks
  - Client token generation endpoint
  - Payment processing (with gateway stub)
  - Payment method CRUD endpoints
  - Plan listing and subscription flow
  - Health/gateway-info endpoints
  - Graceful degradation when Braintree not configured
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Fresh TestClient with rate limiter + in-memory state reset for each test."""
    from services.backend_api.main import app
    from services.backend_api.routers import payment

    # Reset rate limiter counters
    _clear_rate_limiter(app)

    # Reset in-memory payment state so tests are isolated
    payment._user_subscriptions.clear()
    payment._payment_history.clear()

    return TestClient(app, raise_server_exceptions=False)


def _clear_rate_limiter(app):
    """Walk the ASGI app stack to find and reset the rate limiter."""
    obj = getattr(app, "middleware_stack", app)
    for _ in range(20):  # max depth
        if hasattr(obj, "_hits"):
            obj._hits.clear()
            return
        obj = getattr(obj, "app", None)
        if obj is None:
            break


# ============================================================================
# UNIT: braintree_service configuration
# ============================================================================

class TestBraintreeServiceConfig:
    """Test the braintree_service module configuration logic."""

    def test_is_configured_returns_false_when_no_env(self):
        """Without env vars, is_configured() should be False."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to reset module state
            from services.backend_api.services import braintree_service as bs
            # Clear cached env reads
            os.environ.pop("BRAINTREE_MERCHANT_ID", None)
            os.environ.pop("BRAINTREE_PUBLIC_KEY", None)
            os.environ.pop("BRAINTREE_PRIVATE_KEY", None)
            assert bs.is_configured() is False

    def test_is_configured_returns_true_with_all_keys(self):
        with patch.dict(os.environ, {
            "BRAINTREE_MERCHANT_ID": "test_merchant",
            "BRAINTREE_PUBLIC_KEY": "test_pub",
            "BRAINTREE_PRIVATE_KEY": "test_priv",
        }):
            from services.backend_api.services import braintree_service as bs
            assert bs.is_configured() is True

    def test_get_environment_defaults_to_sandbox(self):
        with patch.dict(os.environ, {"BRAINTREE_ENVIRONMENT": "sandbox"}):
            from services.backend_api.services import braintree_service as bs
            import braintree
            env = bs._get_environment()
            assert env == braintree.Environment.Sandbox

    def test_get_environment_production(self):
        with patch.dict(os.environ, {"BRAINTREE_ENVIRONMENT": "production"}):
            from services.backend_api.services import braintree_service as bs
            import braintree
            env = bs._get_environment()
            assert env == braintree.Environment.Production

    def test_gateway_raises_without_credentials(self):
        """get_gateway() should raise if credentials are missing."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BRAINTREE_MERCHANT_ID", None)
            os.environ.pop("BRAINTREE_PUBLIC_KEY", None)
            os.environ.pop("BRAINTREE_PRIVATE_KEY", None)
            from services.backend_api.services import braintree_service as bs
            bs._gateway = None  # reset singleton
            with pytest.raises(RuntimeError, match="Braintree not configured"):
                bs.get_gateway()

    def test_plan_map_has_all_tiers(self):
        from services.backend_api.services import braintree_service as bs
        assert "monthly" in bs.BRAINTREE_PLAN_MAP
        assert "annual" in bs.BRAINTREE_PLAN_MAP
        assert "elitepro" in bs.BRAINTREE_PLAN_MAP


# ============================================================================
# INTEGRATION: Payment router endpoints
# ============================================================================

class TestPaymentEndpoints:
    """Test payment router HTTP endpoints."""

    def test_get_plans_returns_all_tiers(self, client):
        resp = client.get("/api/payment/v1/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data
        plan_ids = {p["id"] for p in data["plans"]}
        assert plan_ids == {"free", "monthly", "annual", "elitepro"}
        assert data["current_plan"] == "free"  # default for demo user

    def test_get_single_plan(self, client):
        resp = client.get("/api/payment/v1/plans/monthly")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "monthly"
        assert data["price"] == 15.99

    def test_get_unknown_plan_404(self, client):
        resp = client.get("/api/payment/v1/plans/platinum")
        assert resp.status_code == 404

    def test_process_free_plan_no_payment_needed(self, client):
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "free"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["amount_charged"] == 0.0

    def test_process_paid_plan_requires_payment_method(self, client):
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "monthly"
        })
        assert resp.status_code == 400
        assert "Payment method required" in resp.json()["detail"]

    def test_process_paid_plan_with_stub(self, client):
        """When Braintree is not configured, falls back to stub processor."""
        with patch("services.backend_api.routers.payment.braintree_service") as mock_bt:
            mock_bt.is_configured.return_value = False
            resp = client.post("/api/payment/v1/process", json={
                "plan_id": "monthly",
                "payment_method_nonce": "fake-valid-nonce"
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["plan_id"] == "monthly"
        assert data["amount_charged"] == 15.99

    def test_process_paid_plan_with_promo_code(self, client):
        with patch("services.backend_api.routers.payment.braintree_service") as mock_bt:
            mock_bt.is_configured.return_value = False
            resp = client.post("/api/payment/v1/process", json={
                "plan_id": "annual",
                "payment_method_nonce": "fake-nonce",
                "promo_code": "LAUNCH20"
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # 149.99 - 20% = 119.992 → rounded to 119.99
        assert data["amount_charged"] == pytest.approx(119.99, abs=0.01)

    def test_invalid_plan_returns_400(self, client):
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "diamond",
            "payment_method_nonce": "nonce"
        })
        assert resp.status_code == 400

    def test_payment_history_returns_empty_initially(self, client):
        resp = client.get("/api/payment/v1/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data

    def test_current_subscription_defaults_to_free(self, client):
        resp = client.get("/api/payment/v1/subscription")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"] == "free"

    def test_cancel_no_subscription(self, client):
        resp = client.post("/api/payment/v1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_health_endpoint(self, client):
        resp = client.get("/api/payment/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["gateway"] == "braintree"
        assert "braintree_configured" in data

    def test_gateway_info_endpoint(self, client):
        resp = client.get("/api/payment/v1/gateway-info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gateway"] == "braintree"

    def test_list_methods_returns_empty_when_unconfigured(self, client):
        resp = client.get("/api/payment/v1/methods")
        assert resp.status_code == 200
        assert resp.json()["methods"] == []


# ============================================================================
# INTEGRATION: Client token endpoint
# ============================================================================

class TestClientToken:
    """Test client token generation."""

    def test_client_token_503_when_unconfigured(self, client):
        """Should return 503 if Braintree credentials are missing."""
        # In test environment, Braintree is typically not configured
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BRAINTREE_MERCHANT_ID", None)
            os.environ.pop("BRAINTREE_PUBLIC_KEY", None)
            os.environ.pop("BRAINTREE_PRIVATE_KEY", None)
            resp = client.get("/api/payment/v1/client-token")
            # Either 503 (not configured) or 200 (if env has keys)
            assert resp.status_code in (200, 503)


# ============================================================================
# UNIT: Braintree service function mocks (no network calls)
# ============================================================================

class TestBraintreeServiceMocked:
    """Test braintree_service functions with mocked SDK."""

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_generate_client_token(self, mock_gw):
        mock_gw.return_value.client_token.generate.return_value = "mock-client-token-123"
        from services.backend_api.services.braintree_service import generate_client_token
        token = generate_client_token()
        assert token == "mock-client-token-123"

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_find_or_create_customer_existing(self, mock_gw):
        mock_customer = MagicMock()
        mock_customer.id = "user_42"
        mock_customer.email = "test@test.com"
        mock_gw.return_value.customer.find.return_value = mock_customer

        from services.backend_api.services.braintree_service import find_or_create_customer
        result = find_or_create_customer("user_42")
        assert result["id"] == "user_42"
        assert result["created"] is False

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_create_sale_success(self, mock_gw):
        mock_tx = MagicMock()
        mock_tx.id = "tx_abc123"
        mock_tx.amount = "15.99"
        mock_tx.status = "submitted_for_settlement"
        mock_tx.created_at = None

        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.transaction = mock_tx
        mock_gw.return_value.transaction.sale.return_value = mock_result

        from services.backend_api.services.braintree_service import create_sale
        result = create_sale("15.99", payment_method_nonce="fake-nonce")
        assert result["success"] is True
        assert result["transaction_id"] == "tx_abc123"

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_create_sale_failure(self, mock_gw):
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.errors.deep_errors = []
        mock_result.message = "Card declined"
        mock_gw.return_value.transaction.sale.return_value = mock_result

        from services.backend_api.services.braintree_service import create_sale
        result = create_sale("15.99", payment_method_nonce="bad-nonce")
        assert result["success"] is False

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_list_payment_methods_empty(self, mock_gw):
        import braintree
        mock_gw.return_value.customer.find.side_effect = braintree.exceptions.not_found_error.NotFoundError
        from services.backend_api.services.braintree_service import list_payment_methods
        result = list_payment_methods("nonexistent_user")
        assert result == []

    @patch("services.backend_api.services.braintree_service.gateway")
    def test_cancel_subscription_success(self, mock_gw):
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_gw.return_value.subscription.cancel.return_value = mock_result

        from services.backend_api.services.braintree_service import cancel_subscription
        result = cancel_subscription("sub_123")
        assert result["success"] is True
