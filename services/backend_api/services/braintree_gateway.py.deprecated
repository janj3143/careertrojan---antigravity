"""
Braintree Payment Gateway Service — CareerTrojan
==================================================
Abstracts all Braintree SDK calls behind a clean interface.

Reads BRAINTREE_ENVIRONMENT to decide sandbox vs production keys:
  - sandbox    → uses BRAINTREE_MERCHANT_ID / PUBLIC / PRIVATE from .env
  - production → same env vars, but values will be the live credentials

Usage:
    from services.braintree_gateway import BraintreeGateway
    gw = BraintreeGateway()          # reads .env automatically
    token = gw.generate_client_token()
    result = gw.create_transaction(amount="15.99", nonce="tokencc_...")

Author: CareerTrojan System
Date:   February 9, 2026
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List

import braintree

logger = logging.getLogger(__name__)


class BraintreeGateway:
    """Thin wrapper around the Braintree Python SDK."""

    def __init__(self) -> None:
        env = os.getenv("BRAINTREE_ENVIRONMENT", "sandbox").strip().lower()
        merchant_id = os.getenv("BRAINTREE_MERCHANT_ID", "")
        public_key = os.getenv("BRAINTREE_PUBLIC_KEY", "")
        private_key = os.getenv("BRAINTREE_PRIVATE_KEY", "")

        if not all([merchant_id, public_key, private_key]):
            logger.warning("Braintree credentials missing — gateway will return errors")

        bt_env = (
            braintree.Environment.Production
            if env == "production"
            else braintree.Environment.Sandbox
        )

        self.gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment=bt_env,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key,
            )
        )
        self.environment = env
        logger.info(f"Braintree gateway initialised ({env})")

    # ── Client Token ─────────────────────────────────────────
    def generate_client_token(self, customer_id: Optional[str] = None) -> str:
        """
        Generate a client token for the frontend Drop-in UI.
        Optionally attach to an existing Braintree customer.
        """
        params: Dict[str, Any] = {}
        if customer_id:
            params["customer_id"] = customer_id
        return self.gateway.client_token.generate(params)

    # ── Customers ────────────────────────────────────────────
    def find_or_create_customer(
        self, user_id: str, email: str, first_name: str = "", last_name: str = ""
    ) -> str:
        """Return existing Braintree customer_id or create one."""
        try:
            customer = self.gateway.customer.find(user_id)
            return customer.id
        except braintree.exceptions.not_found_error.NotFoundError:
            result = self.gateway.customer.create(
                {
                    "id": user_id,
                    "email": email,
                    "first_name": first_name or "CareerTrojan",
                    "last_name": last_name or "User",
                }
            )
            if result.is_success:
                logger.info(f"Created Braintree customer {user_id}")
                return result.customer.id
            raise RuntimeError(f"Braintree customer creation failed: {result.message}")

    # ── Transactions (one-off or subscription start) ─────────
    def create_transaction(
        self,
        amount: str,
        payment_method_nonce: str,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Charge a payment method nonce (from Drop-in UI).
        Returns {"success": bool, "transaction_id": str, "message": str}.
        """
        tx_params: Dict[str, Any] = {
            "amount": amount,
            "payment_method_nonce": payment_method_nonce,
            "options": {"submit_for_settlement": True},
        }
        if customer_id:
            tx_params["customer_id"] = customer_id
        if order_id:
            tx_params["order_id"] = order_id

        result = self.gateway.transaction.sale(tx_params)

        if result.is_success:
            tx = result.transaction
            logger.info(f"Braintree transaction {tx.id} – {tx.status}")
            return {
                "success": True,
                "transaction_id": tx.id,
                "status": tx.status,
                "message": "Payment successful",
            }
        else:
            msg = result.message or "Transaction declined"
            logger.warning(f"Braintree transaction failed: {msg}")
            return {
                "success": False,
                "transaction_id": None,
                "status": "failed",
                "message": msg,
            }

    # ── Subscription (recurring billing) ─────────────────────
    def create_subscription(
        self,
        payment_method_token: str,
        plan_id: str,
        price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a recurring subscription against a Braintree plan.
        Plans must exist in the Braintree Control Panel.
        """
        sub_params: Dict[str, Any] = {
            "payment_method_token": payment_method_token,
            "plan_id": plan_id,
        }
        if price:
            sub_params["price"] = price

        result = self.gateway.subscription.create(sub_params)

        if result.is_success:
            sub = result.subscription
            return {
                "success": True,
                "subscription_id": sub.id,
                "status": sub.status,
                "next_billing_date": str(sub.next_billing_date) if sub.next_billing_date else None,
                "message": "Subscription created",
            }
        return {
            "success": False,
            "subscription_id": None,
            "status": "failed",
            "message": result.message or "Subscription creation failed",
        }

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel an active subscription."""
        result = self.gateway.subscription.cancel(subscription_id)
        if result.is_success:
            return {"success": True, "message": "Subscription cancelled"}
        return {"success": False, "message": result.message or "Cancellation failed"}

    # ── Payment Methods ──────────────────────────────────────
    def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """List saved payment methods for a customer."""
        try:
            customer = self.gateway.customer.find(customer_id)
        except braintree.exceptions.not_found_error.NotFoundError:
            return []

        methods = []
        for pm in customer.payment_methods:
            entry: Dict[str, Any] = {
                "token": pm.token,
                "type": type(pm).__name__,
                "default": pm.default,
            }
            if hasattr(pm, "card_type"):
                entry["card_type"] = pm.card_type
                entry["last_4"] = pm.last_4
                entry["expiration_date"] = pm.expiration_date
            elif hasattr(pm, "email"):
                entry["email"] = pm.email  # PayPal
            methods.append(entry)
        return methods

    def delete_payment_method(self, token: str) -> Dict[str, Any]:
        """Remove a saved payment method."""
        result = self.gateway.payment_method.delete(token)
        # delete returns a SuccessfulResult or raises
        return {"success": True, "message": f"Payment method {token} deleted"}

    # ── Health ───────────────────────────────────────────────
    def health_check(self) -> Dict[str, Any]:
        """Verify connectivity to Braintree."""
        try:
            token = self.gateway.client_token.generate({})
            return {
                "status": "healthy",
                "environment": self.environment,
                "can_generate_token": bool(token),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "environment": self.environment,
                "error": str(e),
            }
