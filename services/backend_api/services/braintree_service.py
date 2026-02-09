"""
Braintree Payment Gateway Service — CareerTrojan
=================================================

Handles all Braintree SDK interactions:
  - Gateway configuration (sandbox ↔ production)
  - Client token generation (for Drop-in UI)
  - Payment method creation (cards, PayPal, etc.)
  - Transaction processing (sale, void, refund)
  - Subscription management (create, cancel, update)
  - Customer management

Env vars required:
  BRAINTREE_ENVIRONMENT   sandbox | production
  BRAINTREE_MERCHANT_ID   merchant ID
  BRAINTREE_PUBLIC_KEY    public key
  BRAINTREE_PRIVATE_KEY   private key
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import braintree

logger = logging.getLogger("payment.braintree")

# ============================================================================
# GATEWAY CONFIGURATION
# ============================================================================

def _get_environment():
    """Return braintree.Environment based on env var."""
    env = os.getenv("BRAINTREE_ENVIRONMENT", "sandbox").lower()
    if env == "production":
        return braintree.Environment.Production
    return braintree.Environment.Sandbox


def get_gateway() -> braintree.BraintreeGateway:
    """
    Create and return a configured Braintree gateway.

    Reads credentials from env vars. Fails loudly if not configured.
    """
    merchant_id = os.getenv("BRAINTREE_MERCHANT_ID")
    public_key = os.getenv("BRAINTREE_PUBLIC_KEY")
    private_key = os.getenv("BRAINTREE_PRIVATE_KEY")

    if not all([merchant_id, public_key, private_key]):
        logger.error("Braintree credentials missing — check .env")
        raise RuntimeError(
            "Braintree not configured. Set BRAINTREE_MERCHANT_ID, "
            "BRAINTREE_PUBLIC_KEY, BRAINTREE_PRIVATE_KEY in .env"
        )

    return braintree.BraintreeGateway(
        braintree.Configuration(
            environment=_get_environment(),
            merchant_id=merchant_id,
            public_key=public_key,
            private_key=private_key,
        )
    )


# Lazy singleton — initialised on first call
_gateway: Optional[braintree.BraintreeGateway] = None


def gateway() -> braintree.BraintreeGateway:
    global _gateway
    if _gateway is None:
        _gateway = get_gateway()
    return _gateway


def is_configured() -> bool:
    """Check whether Braintree creds are present (without connecting)."""
    return all([
        os.getenv("BRAINTREE_MERCHANT_ID"),
        os.getenv("BRAINTREE_PUBLIC_KEY"),
        os.getenv("BRAINTREE_PRIVATE_KEY"),
    ])


# ============================================================================
# CLIENT TOKEN (for Drop-in UI / Hosted Fields on the frontend)
# ============================================================================

def generate_client_token(customer_id: Optional[str] = None) -> str:
    """
    Generate a client token for the Braintree Drop-in UI.

    If customer_id is provided and exists in the Braintree vault,
    the Drop-in will pre-populate saved payment methods.
    """
    gw = gateway()
    kwargs: Dict[str, Any] = {}
    if customer_id:
        kwargs["customer_id"] = customer_id
    token = gw.client_token.generate(kwargs)
    logger.info("Client token generated (customer=%s)", customer_id or "anonymous")
    return token


# ============================================================================
# CUSTOMER MANAGEMENT
# ============================================================================

def find_or_create_customer(
    customer_id: str,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Look up a Braintree customer; create one if it doesn't exist.

    Returns dict with 'id', 'email', 'created'.
    """
    gw = gateway()
    try:
        customer = gw.customer.find(customer_id)
        return {"id": customer.id, "email": customer.email, "created": False}
    except braintree.exceptions.not_found_error.NotFoundError:
        result = gw.customer.create({
            "id": customer_id,
            "email": email or "",
            "first_name": first_name or "",
            "last_name": last_name or "",
        })
        if result.is_success:
            logger.info("Created Braintree customer %s", customer_id)
            return {"id": result.customer.id, "email": result.customer.email, "created": True}
        else:
            errors = [e.message for e in result.errors.deep_errors]
            logger.error("Customer creation failed: %s", errors)
            raise RuntimeError(f"Customer creation failed: {errors}")


# ============================================================================
# PAYMENT METHOD (vault a card / PayPal for future charges)
# ============================================================================

def create_payment_method(
    customer_id: str,
    payment_method_nonce: str,
    make_default: bool = True,
) -> Dict[str, Any]:
    """
    Vault a payment method nonce (from Drop-in UI) to a customer.

    Returns dict with 'token', 'type', 'last4' (if card), 'email' (if PayPal).
    """
    gw = gateway()
    result = gw.payment_method.create({
        "customer_id": customer_id,
        "payment_method_nonce": payment_method_nonce,
        "options": {
            "make_default": make_default,
            "verify_card": True,       # run $0 auth to verify card is real
        },
    })
    if result.is_success:
        pm = result.payment_method
        info: Dict[str, Any] = {"token": pm.token}
        if hasattr(pm, "card_type"):
            info.update({"type": "card", "card_type": pm.card_type, "last4": pm.last_4})
        elif hasattr(pm, "email"):
            info.update({"type": "paypal", "email": pm.email})
        else:
            info["type"] = "other"
        logger.info("Vaulted payment method %s for customer %s", pm.token, customer_id)
        return info
    else:
        errors = [e.message for e in result.errors.deep_errors]
        logger.error("Payment method creation failed: %s", errors)
        raise RuntimeError(f"Payment method creation failed: {errors}")


def list_payment_methods(customer_id: str) -> List[Dict[str, Any]]:
    """List all vaulted payment methods for a customer."""
    gw = gateway()
    try:
        customer = gw.customer.find(customer_id)
    except braintree.exceptions.not_found_error.NotFoundError:
        return []
    methods = []
    for pm in (customer.credit_cards or []):
        methods.append({
            "token": pm.token,
            "type": "card",
            "card_type": pm.card_type,
            "last4": pm.last_4,
            "expiration": f"{pm.expiration_month}/{pm.expiration_year}",
            "default": pm.default,
        })
    for pm in (customer.paypal_accounts or []):
        methods.append({
            "token": pm.token,
            "type": "paypal",
            "email": pm.email,
            "default": pm.default,
        })
    return methods


def delete_payment_method(token: str) -> bool:
    """Remove a vaulted payment method."""
    gw = gateway()
    result = gw.payment_method.delete(token)
    return result.is_success


# ============================================================================
# TRANSACTIONS (one-off charges)
# ============================================================================

def create_sale(
    amount: str,
    payment_method_nonce: Optional[str] = None,
    payment_method_token: Optional[str] = None,
    customer_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Charge a payment method.

    Provide EITHER payment_method_nonce (from Drop-in, one-time use)
    OR payment_method_token (vaulted, reusable).
    """
    gw = gateway()
    tx_data: Dict[str, Any] = {
        "amount": amount,
        "options": {"submit_for_settlement": True},
    }
    if payment_method_nonce:
        tx_data["payment_method_nonce"] = payment_method_nonce
    elif payment_method_token:
        tx_data["payment_method_token"] = payment_method_token
    else:
        raise ValueError("Must provide payment_method_nonce or payment_method_token")

    if customer_id:
        tx_data["customer_id"] = customer_id
    if order_id:
        tx_data["order_id"] = order_id

    result = gw.transaction.sale(tx_data)
    if result.is_success:
        tx = result.transaction
        logger.info("Sale %s — $%s — status=%s", tx.id, tx.amount, tx.status)
        return {
            "success": True,
            "transaction_id": tx.id,
            "amount": str(tx.amount),
            "status": tx.status,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
    else:
        errors = [e.message for e in result.errors.deep_errors]
        msg = result.message if hasattr(result, "message") else str(errors)
        logger.error("Sale failed: %s", msg)
        return {"success": False, "error": msg}


def void_transaction(transaction_id: str) -> Dict[str, Any]:
    """Void an authorized (unsettled) transaction."""
    gw = gateway()
    result = gw.transaction.void(transaction_id)
    if result.is_success:
        return {"success": True, "transaction_id": result.transaction.id, "status": "voided"}
    return {"success": False, "error": result.message}


def refund_transaction(transaction_id: str, amount: Optional[str] = None) -> Dict[str, Any]:
    """Refund a settled transaction (full or partial)."""
    gw = gateway()
    result = gw.transaction.refund(transaction_id, amount)
    if result.is_success:
        return {"success": True, "transaction_id": result.transaction.id, "status": "refunded"}
    return {"success": False, "error": result.message}


def find_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """Look up a transaction by ID."""
    gw = gateway()
    try:
        tx = gw.transaction.find(transaction_id)
        return {
            "id": tx.id,
            "amount": str(tx.amount),
            "status": tx.status,
            "type": tx.type,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "customer_id": tx.customer_details.id if tx.customer_details else None,
        }
    except braintree.exceptions.not_found_error.NotFoundError:
        return None


# ============================================================================
# SUBSCRIPTIONS (recurring billing — uses Braintree Plans)
# ============================================================================

# Map our plan tier IDs to Braintree Plan IDs (create these in Braintree dashboard)
BRAINTREE_PLAN_MAP = {
    "monthly": os.getenv("BRAINTREE_PLAN_MONTHLY", "monthly_pro"),
    "annual": os.getenv("BRAINTREE_PLAN_ANNUAL", "annual_pro"),
    "elitepro": os.getenv("BRAINTREE_PLAN_ELITE", "elite_pro"),
}


def create_subscription(
    plan_id: str,
    payment_method_token: str,
    price_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a recurring subscription.

    plan_id: our internal plan key (monthly, annual, elitepro)
    payment_method_token: vaulted payment method token
    """
    gw = gateway()
    bt_plan_id = BRAINTREE_PLAN_MAP.get(plan_id)
    if not bt_plan_id:
        raise ValueError(f"Unknown plan: {plan_id}")

    sub_data: Dict[str, Any] = {
        "payment_method_token": payment_method_token,
        "plan_id": bt_plan_id,
    }
    if price_override:
        sub_data["price"] = price_override

    result = gw.subscription.create(sub_data)
    if result.is_success:
        sub = result.subscription
        logger.info("Subscription %s created for plan %s", sub.id, bt_plan_id)
        return {
            "success": True,
            "subscription_id": sub.id,
            "plan_id": plan_id,
            "status": sub.status,
            "next_billing_date": str(sub.next_billing_date) if sub.next_billing_date else None,
            "price": str(sub.price),
        }
    else:
        errors = [e.message for e in result.errors.deep_errors]
        return {"success": False, "error": str(errors)}


def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
    """Cancel a Braintree subscription."""
    gw = gateway()
    result = gw.subscription.cancel(subscription_id)
    if result.is_success:
        logger.info("Subscription %s cancelled", subscription_id)
        return {"success": True, "subscription_id": subscription_id, "status": "cancelled"}
    return {"success": False, "error": result.message}


def find_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
    """Look up subscription details."""
    gw = gateway()
    try:
        sub = gw.subscription.find(subscription_id)
        return {
            "id": sub.id,
            "plan_id": sub.plan_id,
            "status": sub.status,
            "price": str(sub.price),
            "next_billing_date": str(sub.next_billing_date) if sub.next_billing_date else None,
            "payment_method_token": sub.payment_method_token,
        }
    except braintree.exceptions.not_found_error.NotFoundError:
        return None
