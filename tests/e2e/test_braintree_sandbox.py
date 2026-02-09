"""
End-to-end Braintree Sandbox Tests — CareerTrojan
===================================================

These tests hit the REAL Braintree sandbox API.
They require valid sandbox credentials in .env:
  BRAINTREE_ENVIRONMENT=sandbox
  BRAINTREE_MERCHANT_ID=...
  BRAINTREE_PUBLIC_KEY=...
  BRAINTREE_PRIVATE_KEY=...

Braintree sandbox test nonces:
  - fake-valid-nonce                → successful transaction
  - fake-valid-visa-nonce           → successful Visa transaction
  - fake-valid-mastercard-nonce     → successful Mastercard
  - fake-paypal-one-time-nonce      → successful PayPal
  - fake-processor-declined-nonce   → processor decline
  - fake-gateway-rejected-fraud-nonce → gateway rejection (fraud)

Run with:  pytest tests/e2e/test_braintree_sandbox.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Skip entire module if Braintree not configured
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("BRAINTREE_MERCHANT_ID"),
        os.getenv("BRAINTREE_PUBLIC_KEY"),
        os.getenv("BRAINTREE_PRIVATE_KEY"),
    ]),
    reason="Braintree sandbox credentials not set in .env",
)


@pytest.fixture(scope="module")
def service():
    """Get the braintree_service module (with real sandbox creds)."""
    from services.backend_api.services import braintree_service
    assert braintree_service.is_configured(), "Braintree not configured"
    return braintree_service


@pytest.fixture(scope="module")
def gw(service):
    """Get a configured gateway."""
    return service.gateway()


# ============================================================================
# 1. CLIENT TOKEN
# ============================================================================

class TestClientToken:
    def test_generate_client_token_anonymous(self, service):
        """Generate a client token without a customer ID."""
        token = service.generate_client_token()
        assert token is not None
        assert len(token) > 20  # JWT-like string
        print(f"  ✓ Client token generated ({len(token)} chars)")

    def test_generate_client_token_with_new_customer(self, service):
        """Generate token for a new customer (auto-created)."""
        import uuid
        cust_id = f"test_ct_{uuid.uuid4().hex[:8]}"
        # Create customer first
        customer = service.find_or_create_customer(cust_id, email="test@careertrojan.com")
        assert customer["id"] == cust_id
        assert customer["created"] is True

        # Now generate token for that customer
        token = service.generate_client_token(customer_id=cust_id)
        assert token is not None
        assert len(token) > 20
        print(f"  ✓ Client token for customer {cust_id} ({len(token)} chars)")


# ============================================================================
# 2. CUSTOMER MANAGEMENT
# ============================================================================

class TestCustomerManagement:
    def test_create_customer(self, service):
        import uuid
        cust_id = f"test_cust_{uuid.uuid4().hex[:8]}"
        result = service.find_or_create_customer(
            cust_id,
            email="e2e@careertrojan.com",
            first_name="E2E",
            last_name="Test",
        )
        assert result["id"] == cust_id
        assert result["created"] is True
        print(f"  ✓ Customer {cust_id} created")

    def test_find_existing_customer(self, service):
        import uuid
        cust_id = f"test_find_{uuid.uuid4().hex[:8]}"
        # Create
        service.find_or_create_customer(cust_id, email="find@careertrojan.com")
        # Find again
        result = service.find_or_create_customer(cust_id)
        assert result["id"] == cust_id
        assert result["created"] is False
        print(f"  ✓ Customer {cust_id} found (not re-created)")


# ============================================================================
# 3. TRANSACTIONS (sale / refund / void)
# ============================================================================

class TestTransactions:
    def test_successful_sale_with_nonce(self, service):
        """Process a $1.00 sale using Braintree's fake-valid-nonce."""
        result = service.create_sale(
            amount="1.00",
            payment_method_nonce="fake-valid-nonce",
        )
        assert result["success"] is True
        assert result["transaction_id"] is not None
        assert result["status"] in ("submitted_for_settlement", "authorized", "settling")
        print(f"  ✓ Sale {result['transaction_id']} — ${result['amount']} — {result['status']}")

    def test_sale_with_visa_nonce(self, service):
        """Sale with Visa test nonce."""
        result = service.create_sale(
            amount="9.99",
            payment_method_nonce="fake-valid-visa-nonce",
        )
        assert result["success"] is True
        print(f"  ✓ Visa sale {result['transaction_id']} — ${result['amount']}")

    def test_sale_with_mastercard_nonce(self, service):
        """Sale with Mastercard test nonce."""
        result = service.create_sale(
            amount="14.99",
            payment_method_nonce="fake-valid-mastercard-nonce",
        )
        assert result["success"] is True
        print(f"  ✓ Mastercard sale {result['transaction_id']} — ${result['amount']}")

    def test_declined_nonce(self, service):
        """Sale with a nonce that declines — should fail cleanly."""
        result = service.create_sale(
            amount="2000.00",
            payment_method_nonce="fake-processor-declined-nonce",
        )
        assert result["success"] is False
        assert "error" in result or "message" in str(result)
        print(f"  ✓ Declined as expected: {result.get('error', 'declined')}")

    def test_find_transaction(self, service):
        """Create a sale then look it up."""
        sale = service.create_sale(amount="0.50", payment_method_nonce="fake-valid-nonce")
        assert sale["success"] is True
        tx_id = sale["transaction_id"]

        found = service.find_transaction(tx_id)
        assert found is not None
        assert found["id"] == tx_id
        assert found["amount"] == "0.50"
        print(f"  ✓ Found transaction {tx_id}: ${found['amount']} status={found['status']}")

    def test_void_transaction(self, service):
        """Create a sale and void it before settlement."""
        sale = service.create_sale(amount="0.25", payment_method_nonce="fake-valid-nonce")
        assert sale["success"] is True
        tx_id = sale["transaction_id"]

        void = service.void_transaction(tx_id)
        assert void["success"] is True
        assert void["status"] == "voided"
        print(f"  ✓ Voided transaction {tx_id}")


# ============================================================================
# 4. PAYMENT METHODS (vault)
# ============================================================================

class TestPaymentMethods:
    def test_vault_and_list_card(self, service):
        """Vault a card via nonce and list it back."""
        import uuid
        cust_id = f"test_vault_{uuid.uuid4().hex[:8]}"
        service.find_or_create_customer(cust_id, email="vault@careertrojan.com")

        method = service.create_payment_method(cust_id, "fake-valid-visa-nonce")
        assert "token" in method
        assert method["type"] == "card"
        print(f"  ✓ Vaulted card {method.get('card_type')} ****{method.get('last4')} → token={method['token']}")

        # List
        methods = service.list_payment_methods(cust_id)
        assert len(methods) >= 1
        tokens = [m["token"] for m in methods]
        assert method["token"] in tokens
        print(f"  ✓ Listed {len(methods)} method(s) for customer {cust_id}")

    def test_delete_payment_method(self, service):
        """Vault then delete a payment method."""
        import uuid
        cust_id = f"test_del_{uuid.uuid4().hex[:8]}"
        service.find_or_create_customer(cust_id, email="del@careertrojan.com")

        method = service.create_payment_method(cust_id, "fake-valid-nonce")
        token = method["token"]

        # Delete
        success = service.delete_payment_method(token)
        assert success is True
        print(f"  ✓ Deleted payment method {token}")

    def test_pay_with_vaulted_token(self, service):
        """Vault a card, then use its token for a sale."""
        import uuid
        cust_id = f"test_pay_vault_{uuid.uuid4().hex[:8]}"
        service.find_or_create_customer(cust_id, email="payvault@careertrojan.com")

        method = service.create_payment_method(cust_id, "fake-valid-visa-nonce")
        token = method["token"]

        # Sale using vaulted token
        sale = service.create_sale(
            amount="5.00",
            payment_method_token=token,
            customer_id=cust_id,
        )
        assert sale["success"] is True
        print(f"  ✓ Sale with vaulted token: {sale['transaction_id']} — ${sale['amount']}")


# ============================================================================
# 5. FULL FLOW: nonce → sale → find → void
# ============================================================================

class TestFullFlow:
    def test_nonce_to_sale_to_lookup(self, service):
        """
        Simulate the complete Drop-in UI flow:
          1. Client sends nonce from Drop-in UI
          2. Server creates a sale with the nonce
          3. Server looks up the transaction
          4. Server voids the transaction
        """
        print("\n  ── Full Flow Test ──")

        # Step 1: "Receive" the nonce (in real life, Drop-in UI sends this)
        nonce = "fake-valid-nonce"
        print(f"  1. Nonce received: {nonce}")

        # Step 2: Create sale
        sale = service.create_sale(
            amount="15.99",
            payment_method_nonce=nonce,
            order_id="order_e2e_test",
        )
        assert sale["success"] is True
        tx_id = sale["transaction_id"]
        print(f"  2. Sale created: {tx_id} — ${sale['amount']} — status={sale['status']}")

        # Step 3: Look up transaction
        tx = service.find_transaction(tx_id)
        assert tx is not None
        assert tx["id"] == tx_id
        print(f"  3. Transaction found: {tx['id']} — status={tx['status']}")

        # Step 4: Void (cleanup — don't leave test transactions in settlement)
        void = service.void_transaction(tx_id)
        assert void["success"] is True
        print(f"  4. Transaction voided: {void['status']}")
        print("  ── Full Flow Complete ✓ ──")

    def test_vault_flow(self, service):
        """
        Full vault flow:
          1. Create customer
          2. Vault a card
          3. Pay with vaulted card
          4. Find the transaction
          5. Void and cleanup
        """
        import uuid
        print("\n  ── Vault Flow Test ──")

        cust_id = f"e2e_vault_{uuid.uuid4().hex[:8]}"

        # 1. Create customer
        cust = service.find_or_create_customer(cust_id, email="e2eflow@careertrojan.com")
        assert cust["created"] is True
        print(f"  1. Customer created: {cust_id}")

        # 2. Vault card
        method = service.create_payment_method(cust_id, "fake-valid-visa-nonce")
        print(f"  2. Card vaulted: {method.get('card_type')} ****{method.get('last4')}")

        # 3. Pay with vaulted card
        sale = service.create_sale(
            amount="149.99",
            payment_method_token=method["token"],
            customer_id=cust_id,
            order_id=f"order_{cust_id}",
        )
        assert sale["success"] is True
        print(f"  3. Sale: {sale['transaction_id']} — ${sale['amount']}")

        # 4. Find it
        tx = service.find_transaction(sale["transaction_id"])
        assert tx is not None
        print(f"  4. Verified: {tx['status']}")

        # 5. Void
        void = service.void_transaction(sale["transaction_id"])
        assert void["success"] is True
        print(f"  5. Voided — cleanup done")

        # Bonus: Delete vaulted method
        service.delete_payment_method(method["token"])
        print("  6. Payment method removed")
        print("  ── Vault Flow Complete ✓ ──")


# ============================================================================
# 6. HTTP ENDPOINT E2E (via TestClient → real Braintree)
# ============================================================================

class TestHTTPEndpoints:
    """Hit the FastAPI endpoints which in turn call Braintree sandbox."""

    @pytest.fixture
    def client(self):
        from services.backend_api.main import app
        from fastapi.testclient import TestClient
        from services.backend_api.routers import payment

        # Reset rate limiter
        obj = getattr(app, "middleware_stack", app)
        for _ in range(20):
            if hasattr(obj, "_hits"):
                obj._hits.clear()
                break
            obj = getattr(obj, "app", None)
            if obj is None:
                break

        payment._user_subscriptions.clear()
        payment._payment_history.clear()
        return TestClient(app, raise_server_exceptions=False)

    def test_client_token_endpoint(self, client):
        """GET /client-token should return a real Braintree client token."""
        resp = client.get("/api/payment/v1/client-token")
        assert resp.status_code == 200
        data = resp.json()
        assert "client_token" in data
        assert len(data["client_token"]) > 20
        print(f"  ✓ /client-token returned {len(data['client_token'])}-char token")

    def test_process_payment_with_nonce(self, client):
        """POST /process with a fake nonce should create a real sandbox transaction."""
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "monthly",
            "payment_method_nonce": "fake-valid-nonce",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["plan_id"] == "monthly"
        assert data["amount_charged"] == 15.99
        print(f"  ✓ /process → subscription={data['subscription_id']} amount=${data['amount_charged']}")

    def test_process_payment_with_promo(self, client):
        """POST /process with promo code applies 20% discount on real transaction."""
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "annual",
            "payment_method_nonce": "fake-valid-visa-nonce",
            "promo_code": "LAUNCH20",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        expected = round(149.99 * 0.80, 2)
        assert data["amount_charged"] == expected
        print(f"  ✓ /process with LAUNCH20 → ${data['amount_charged']} (was $149.99)")

    def test_process_declined_nonce(self, client):
        """POST /process with declined nonce should return 402."""
        resp = client.post("/api/payment/v1/process", json={
            "plan_id": "monthly",
            "payment_method_nonce": "fake-processor-declined-nonce",
        })
        assert resp.status_code == 402
        print(f"  ✓ /process with declined nonce → 402")

    def test_gateway_info(self, client):
        """GET /gateway-info returns sandbox config."""
        resp = client.get("/api/payment/v1/gateway-info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gateway"] == "braintree"
        assert data["configured"] is True
        assert data["environment"] == "sandbox"
        print(f"  ✓ /gateway-info → {data['environment']}, merchant={data['merchant_id']}")
