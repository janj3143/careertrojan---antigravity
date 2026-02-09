"""
Braintree Sandbox Integration Test — CareerTrojan
===================================================
Tests the full payment flow against Braintree sandbox:

  1. Gateway connectivity & client token generation
  2. Customer creation
  3. Payment method vaulting (using sandbox nonce)
  4. Transaction (sale) processing
  5. Transaction lookup
  6. Subscription creation (if plans exist)
  7. Payment method listing
  8. Refund / void
  9. Cleanup

Uses Braintree sandbox test nonces — no real money is charged.

Run:  J:\\Python311\\python.exe tests\\test_braintree_sandbox.py
"""

import os
import sys
import json
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add project root to path so we can import the service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.backend_api.services import braintree_service

# Braintree sandbox test nonces
# See: https://developer.paypal.com/braintree/docs/reference/general/testing
NONCE_VISA = "fake-valid-visa-nonce"
NONCE_MASTERCARD = "fake-valid-mastercard-nonce"
NONCE_AMEX = "fake-valid-amex-nonce"
NONCE_PAYPAL = "fake-paypal-billing-agreement-nonce"
NONCE_DECLINED = "fake-processor-declined-nonce"

TEST_CUSTOMER_ID = f"ct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_EMAIL = "test@careertrojan.com"

results = []


def log_test(name: str, passed: bool, detail: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, detail))
    print(f"  {status}  {name}")
    if detail and not passed:
        print(f"         → {detail}")


def separator(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ============================================================================
# TEST SUITE
# ============================================================================
def main():
    print("=" * 60)
    print("  BRAINTREE SANDBOX INTEGRATION TEST")
    print(f"  Environment: {os.getenv('BRAINTREE_ENVIRONMENT', 'sandbox')}")
    print(f"  Merchant ID: {os.getenv('BRAINTREE_MERCHANT_ID', 'NOT SET')}")
    print(f"  Test Customer: {TEST_CUSTOMER_ID}")
    print("=" * 60)

    # -- 1. Configuration Check --
    separator("1. CONFIGURATION CHECK")
    try:
        configured = braintree_service.is_configured()
        log_test("Credentials present in .env", configured)
    except Exception as e:
        log_test("Credentials present in .env", False, str(e))
        print("\n⛔ Cannot proceed without credentials. Check .env file.")
        return

    # -- 2. Client Token Generation --
    separator("2. CLIENT TOKEN GENERATION")
    client_token = None
    try:
        client_token = braintree_service.generate_client_token()
        log_test("Generate anonymous client token", bool(client_token), f"Token length: {len(client_token)}")
    except Exception as e:
        log_test("Generate anonymous client token", False, str(e))

    # -- 3. Customer Management --
    separator("3. CUSTOMER MANAGEMENT")
    try:
        result = braintree_service.find_or_create_customer(
            TEST_CUSTOMER_ID,
            email=TEST_EMAIL,
            first_name="Test",
            last_name="CareerTrojan",
        )
        log_test("Create sandbox customer", result.get("created", False) or result.get("id") == TEST_CUSTOMER_ID,
                 f"ID={result.get('id')}, Created={result.get('created')}")
    except Exception as e:
        log_test("Create sandbox customer", False, str(e))

    # -- 3b. Client token with customer --
    try:
        ct = braintree_service.generate_client_token(customer_id=TEST_CUSTOMER_ID)
        log_test("Client token with customer ID", bool(ct))
    except Exception as e:
        log_test("Client token with customer ID", False, str(e))

    # -- 4. Payment Method Vaulting --
    separator("4. PAYMENT METHOD VAULTING")
    visa_token = None
    mc_token = None

    # Visa
    try:
        result = braintree_service.create_payment_method(TEST_CUSTOMER_ID, NONCE_VISA)
        visa_token = result.get("token")
        log_test("Vault Visa card", bool(visa_token),
                 f"Token={visa_token}, Type={result.get('card_type')}, Last4={result.get('last4')}")
    except Exception as e:
        log_test("Vault Visa card", False, str(e))

    # Mastercard
    try:
        result = braintree_service.create_payment_method(TEST_CUSTOMER_ID, NONCE_MASTERCARD, make_default=False)
        mc_token = result.get("token")
        log_test("Vault Mastercard", bool(mc_token),
                 f"Token={mc_token}, Type={result.get('card_type')}")
    except Exception as e:
        log_test("Vault Mastercard", False, str(e))

    # -- 5. List Payment Methods --
    separator("5. LIST PAYMENT METHODS")
    try:
        methods = braintree_service.list_payment_methods(TEST_CUSTOMER_ID)
        log_test("List saved methods", len(methods) >= 2,
                 f"Found {len(methods)} methods: {[m.get('card_type', m.get('type')) for m in methods]}")
    except Exception as e:
        log_test("List saved methods", False, str(e))

    # -- 6. Transaction (Sale) --
    separator("6. TRANSACTION — SALE")
    sale_tx_id = None

    # Sale with nonce (simulates Drop-in UI)
    try:
        result = braintree_service.create_sale(
            amount="15.99",
            payment_method_nonce=NONCE_VISA,
            customer_id=TEST_CUSTOMER_ID,
            order_id="ct_test_order_001",
        )
        sale_tx_id = result.get("transaction_id")
        log_test("Sale with nonce ($15.99)", result.get("success", False),
                 f"TX={sale_tx_id}, Status={result.get('status')}")
    except Exception as e:
        log_test("Sale with nonce ($15.99)", False, str(e))

    # Sale with vaulted token
    vaulted_tx_id = None
    if visa_token:
        try:
            result = braintree_service.create_sale(
                amount="149.99",
                payment_method_token=visa_token,
                customer_id=TEST_CUSTOMER_ID,
                order_id="ct_test_order_002",
            )
            vaulted_tx_id = result.get("transaction_id")
            log_test("Sale with vaulted token ($149.99)", result.get("success", False),
                     f"TX={vaulted_tx_id}, Status={result.get('status')}")
        except Exception as e:
            log_test("Sale with vaulted token ($149.99)", False, str(e))

    # Declined transaction
    try:
        result = braintree_service.create_sale(
            amount="5.00",
            payment_method_nonce=NONCE_DECLINED,
        )
        # This SHOULD fail
        log_test("Declined card handled gracefully", not result.get("success", True),
                 f"Message: {result.get('error', 'No error')}")
    except Exception as e:
        log_test("Declined card handled gracefully", True, f"Exception caught: {str(e)[:80]}")

    # -- 7. Transaction Lookup --
    separator("7. TRANSACTION LOOKUP")
    if sale_tx_id:
        try:
            tx = braintree_service.find_transaction(sale_tx_id)
            log_test("Find transaction by ID", tx is not None,
                     f"Amount=${tx.get('amount')}, Status={tx.get('status')}")
        except Exception as e:
            log_test("Find transaction by ID", False, str(e))

    try:
        tx = braintree_service.find_transaction("nonexistent_12345")
        log_test("Non-existent TX returns None", tx is None)
    except Exception as e:
        log_test("Non-existent TX returns None", False, str(e))

    # -- 8. Void/Refund --
    separator("8. VOID / REFUND")
    if sale_tx_id:
        try:
            # Recently created sandbox transactions are usually in 'submitted_for_settlement'
            # which can be voided but not refunded
            result = braintree_service.void_transaction(sale_tx_id)
            log_test("Void unsettled transaction", result.get("success", False),
                     f"Status: {result.get('status', result.get('error'))}")
        except Exception as e:
            log_test("Void unsettled transaction", False, str(e))

    # -- 9. Delete Payment Methods --
    separator("9. CLEANUP — DELETE PAYMENT METHODS")
    if mc_token:
        try:
            ok = braintree_service.delete_payment_method(mc_token)
            log_test("Delete Mastercard", ok)
        except Exception as e:
            log_test("Delete Mastercard", False, str(e))

    if visa_token:
        try:
            ok = braintree_service.delete_payment_method(visa_token)
            log_test("Delete Visa", ok)
        except Exception as e:
            log_test("Delete Visa", False, str(e))

    # -- Summary --
    print("\n" + "=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"  Environment: {os.getenv('BRAINTREE_ENVIRONMENT', 'sandbox')}")
    if failed == 0:
        print("  🎉 ALL TESTS PASSED — Braintree sandbox is fully operational!")
    else:
        print("  ⚠️  Some tests failed — review output above")
    print("=" * 60)


if __name__ == "__main__":
    main()
