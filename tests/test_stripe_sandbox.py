"""
Stripe Sandbox Integration Test — CareerTrojan
================================================
Tests the Stripe payment flow in test mode for comparison with Braintree.

Run:  J:\\Python311\\python.exe tests\\test_stripe_sandbox.py
"""

import os
import sys
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import stripe

# Stripe test key from .env
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
if not STRIPE_KEY.startswith("sk_test_"):
    print("⛔ STRIPE_SECRET_KEY not found or not a test key. Check .env")
    sys.exit(1)
stripe.api_key = STRIPE_KEY

# Stripe test card tokens
# See: https://docs.stripe.com/testing
TOKEN_VISA = "tok_visa"
TOKEN_MASTERCARD = "tok_mastercard"
TOKEN_AMEX = "tok_amex"
TOKEN_DECLINED = "tok_chargeDeclined"

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


def main():
    print("=" * 60)
    print("  STRIPE TEST-MODE INTEGRATION TEST")
    print(f"  API Key: {stripe.api_key[:12]}...{stripe.api_key[-4:]}" if stripe.api_key else "  API Key: NOT SET")
    print("=" * 60)

    if not stripe.api_key or not stripe.api_key.startswith("sk_test_"):
        print("\n⛔ No Stripe test key found. Check .env for 'Stripe API=sk_test_...'")
        return

    # -- 1. Config --
    separator("1. CONFIGURATION")
    log_test("Stripe test key present", True, f"Key prefix: {stripe.api_key[:15]}...")

    # -- 2. Customer --
    separator("2. CUSTOMER CREATION")
    customer = None
    try:
        customer = stripe.Customer.create(
            email="test@careertrojan.com",
            name="Test CareerTrojan",
            metadata={"source": "sandbox_test"},
        )
        log_test("Create customer", bool(customer.id), f"ID={customer.id}")
    except Exception as e:
        log_test("Create customer", False, str(e))

    # -- 3. Payment Method (attach card) --
    separator("3. PAYMENT METHOD")
    pm = None
    try:
        pm = stripe.PaymentMethod.create(
            type="card",
            card={"token": TOKEN_VISA},
        )
        log_test("Create Visa PaymentMethod", bool(pm.id), f"PM={pm.id}, Last4={pm.card.last4}")
    except Exception as e:
        log_test("Create Visa PaymentMethod", False, str(e))

    if pm and customer:
        try:
            stripe.PaymentMethod.attach(pm.id, customer=customer.id)
            log_test("Attach PM to customer", True)
        except Exception as e:
            log_test("Attach PM to customer", False, str(e))

    # -- 4. PaymentIntent (one-off charge) --
    separator("4. PAYMENT INTENT (ONE-OFF)")
    pi = None
    try:
        pi = stripe.PaymentIntent.create(
            amount=1599,  # $15.99 in cents
            currency="gbp",
            customer=customer.id if customer else None,
            payment_method=pm.id if pm else None,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={"order_id": "ct_test_001"},
        )
        log_test("Create & confirm PaymentIntent ($15.99)",
                 pi.status in ("succeeded", "requires_capture"),
                 f"PI={pi.id}, Status={pi.status}")
    except Exception as e:
        log_test("Create & confirm PaymentIntent ($15.99)", False, str(e))

    # -- 5. Retrieve PI --
    separator("5. TRANSACTION LOOKUP")
    if pi:
        try:
            found = stripe.PaymentIntent.retrieve(pi.id)
            log_test("Retrieve PaymentIntent", found.id == pi.id,
                     f"Amount={found.amount}, Status={found.status}")
        except Exception as e:
            log_test("Retrieve PaymentIntent", False, str(e))

    # -- 6. Refund --
    separator("6. REFUND")
    if pi and pi.status == "succeeded":
        try:
            refund = stripe.Refund.create(payment_intent=pi.id)
            log_test("Full refund", refund.status in ("succeeded", "pending"),
                     f"Refund={refund.id}, Status={refund.status}")
        except Exception as e:
            log_test("Full refund", False, str(e))

    # -- 7. Declined card --
    separator("7. DECLINED CARD")
    try:
        declined = stripe.PaymentIntent.create(
            amount=500,
            currency="gbp",
            payment_method_types=["card"],
            payment_method_data={"type": "card", "card": {"token": TOKEN_DECLINED}},
            confirm=True,
        )
        log_test("Declined card returns error", False, f"Unexpectedly succeeded: {declined.status}")
    except stripe.CardError as e:
        log_test("Declined card caught as CardError", True, f"Code={e.code}, Message={e.user_message}")
    except Exception as e:
        log_test("Declined card caught as error", True, f"{type(e).__name__}: {str(e)[:80]}")

    # -- 8. Subscription (requires a Price/Product) --
    separator("8. SUBSCRIPTION (optional)")
    try:
        product = stripe.Product.create(name="CT Pro Monthly Test", metadata={"test": "true"})
        price = stripe.Price.create(
            unit_amount=999,
            currency="gbp",
            recurring={"interval": "month"},
            product=product.id,
        )
        if customer and pm:
            stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": pm.id})
            sub = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price.id}],
                default_payment_method=pm.id,
            )
            log_test("Create subscription", sub.status in ("active", "trialing"),
                     f"Sub={sub.id}, Status={sub.status}")
            # Cancel immediately
            cancelled = stripe.Subscription.cancel(sub.id)
            log_test("Cancel subscription", cancelled.status == "canceled",
                     f"Status={cancelled.status}")
        else:
            log_test("Create subscription", False, "No customer/PM")
    except Exception as e:
        log_test("Subscription flow", False, str(e)[:100])

    # -- 9. Cleanup --
    separator("9. CLEANUP")
    if customer:
        try:
            stripe.Customer.delete(customer.id)
            log_test("Delete test customer", True)
        except Exception as e:
            log_test("Delete test customer", False, str(e))

    # -- Summary --
    print("\n" + "=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("  🎉 ALL TESTS PASSED — Stripe test mode is fully operational!")
    else:
        print("  ⚠️  Some tests failed — review output above")
    print("=" * 60)

    # -- Comparison notes --
    print("\n─── BRAINTREE vs STRIPE COMPARISON ───")
    print("""
  Feature              │ Braintree                    │ Stripe
  ─────────────────────┼──────────────────────────────┼──────────────────────────
  SDK                  │ braintree 4.42.0 (Python)    │ stripe 14.3.0 (Python)
  Drop-in UI           │ Yes (CDN JS widget)          │ Stripe Elements / Checkout
  Pricing              │ 1.9% + 20p (UK cards)        │ 1.5% + 20p (UK cards)
  PayPal integration   │ Native (same merchant)       │ Separate / via link
  Apple/Google Pay     │ Built into Drop-in           │ Via Payment Request Button
  Vault / Save cards   │ Yes (customer-based)         │ Yes (SetupIntent + PM)
  Subscriptions        │ Needs plans in dashboard     │ Dynamic price objects
  Webhooks             │ Yes                          │ Yes
  PCI compliance       │ SAQ A (Drop-in)              │ SAQ A (Elements)
  Go-live cost         │ Free sandbox → live toggle   │ Free sandbox → live toggle
  Verdict              │ Simpler for PayPal + cards   │ More flexible APIs
""")


if __name__ == "__main__":
    main()
