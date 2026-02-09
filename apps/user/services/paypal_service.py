"""
PayPal Payment Integration Service for IntelliCV Platform

This service provides complete PayPal integration for subscription payments,
including subscription creation, management, webhooks, and cancellations.

Features:
- PayPal subscription creation and management
- Webhook handling for payment events
- Plan management (Pro/Expert Monthly/Annual)
- Subscription status tracking
- Refund processing
- Sandbox/Production mode switching

Author: IntelliCV Development Team
Date: October 28, 2025
Version: 1.0.0
"""

import os
import json
import requests
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hmac
import hashlib


class PayPalService:
    """PayPal payment integration service"""
    
    def __init__(self, sandbox_mode: bool = True):
        """
        Initialize PayPal service
        
        Args:
            sandbox_mode: If True, use PayPal sandbox. If False, use production.
        """
        self.sandbox_mode = sandbox_mode
        
        # PayPal API endpoints
        if sandbox_mode:
            self.base_url = "https://api-m.sandbox.paypal.com"
            self.client_id = os.getenv("PAYPAL_SANDBOX_CLIENT_ID", "")
            self.client_secret = os.getenv("PAYPAL_SANDBOX_CLIENT_SECRET", "")
        else:
            self.base_url = "https://api-m.paypal.com"
            self.client_id = os.getenv("PAYPAL_CLIENT_ID", "")
            self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
        
        # Webhook ID for signature verification
        self.webhook_id = os.getenv("PAYPAL_WEBHOOK_ID", "")
        
        # Data storage
        self.data_dir = Path(__file__).parent.parent / "data" / "paypal"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.webhooks_file = self.data_dir / "webhook_events.json"
        
        # PayPal plan IDs (create these in PayPal dashboard)
        self.plan_ids = {
            "pro_monthly": os.getenv("PAYPAL_PLAN_PRO_MONTHLY", ""),
            "expert_monthly": os.getenv("PAYPAL_PLAN_EXPERT_MONTHLY", ""),
            "pro_annual": os.getenv("PAYPAL_PLAN_PRO_ANNUAL", ""),
            "expert_annual": os.getenv("PAYPAL_PLAN_EXPERT_ANNUAL", "")
        }
        
        # Initialize storage
        self._init_storage()
    
    def _init_storage(self):
        """Initialize JSON storage files"""
        if not self.subscriptions_file.exists():
            self.subscriptions_file.write_text(json.dumps({}, indent=2))
        
        if not self.webhooks_file.exists():
            self.webhooks_file.write_text(json.dumps([], indent=2))
    
    def _load_subscriptions(self) -> Dict:
        """Load subscriptions from JSON storage"""
        try:
            return json.loads(self.subscriptions_file.read_text())
        except:
            return {}
    
    def _save_subscriptions(self, subscriptions: Dict):
        """Save subscriptions to JSON storage"""
        self.subscriptions_file.write_text(json.dumps(subscriptions, indent=2))
    
    def _load_webhook_events(self) -> List:
        """Load webhook events from JSON storage"""
        try:
            return json.loads(self.webhooks_file.read_text())
        except:
            return []
    
    def _save_webhook_event(self, event: Dict):
        """Save a webhook event to JSON storage"""
        events = self._load_webhook_events()
        events.append({
            "event_id": event.get("id"),
            "event_type": event.get("event_type"),
            "timestamp": datetime.now().isoformat(),
            "data": event
        })
        # Keep only last 1000 events
        events = events[-1000:]
        self.webhooks_file.write_text(json.dumps(events, indent=2))
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get PayPal OAuth access token
        
        Returns:
            Access token string or None if failed
        """
        if not self.client_id or not self.client_secret:
            return None
        
        url = f"{self.base_url}/v1/oauth2/token"
        
        # Create basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            print(f"Error getting PayPal access token: {e}")
            return None
    
    def create_subscription(
        self,
        user_email: str,
        user_id: str,
        plan_type: str,
        return_url: str,
        cancel_url: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a PayPal subscription
        
        Args:
            user_email: User's email address
            user_id: User ID
            plan_type: Plan type (pro_monthly, expert_monthly, pro_annual, expert_annual)
            return_url: URL to return to after successful subscription
            cancel_url: URL to return to if user cancels
        
        Returns:
            Tuple of (success, subscription_id, approval_url)
        """
        access_token = self._get_access_token()
        if not access_token:
            return False, None, "Failed to authenticate with PayPal"
        
        plan_id = self.plan_ids.get(plan_type)
        if not plan_id:
            return False, None, f"Invalid plan type: {plan_type}"
        
        url = f"{self.base_url}/v1/billing/subscriptions"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "plan_id": plan_id,
            "subscriber": {
                "email_address": user_email
            },
            "application_context": {
                "brand_name": "IntelliCV",
                "locale": "en-GB",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "custom_id": user_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            subscription_id = data.get("id")
            
            # Find approval URL
            approval_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            # Save subscription
            subscriptions = self._load_subscriptions()
            subscriptions[subscription_id] = {
                "user_id": user_id,
                "user_email": user_email,
                "plan_type": plan_type,
                "subscription_id": subscription_id,
                "status": "APPROVAL_PENDING",
                "created_at": datetime.now().isoformat(),
                "approval_url": approval_url
            }
            self._save_subscriptions(subscriptions)
            
            return True, subscription_id, approval_url
            
        except Exception as e:
            return False, None, f"PayPal API error: {str(e)}"
    
    def get_subscription_details(self, subscription_id: str) -> Optional[Dict]:
        """
        Get subscription details from PayPal
        
        Args:
            subscription_id: PayPal subscription ID
        
        Returns:
            Subscription details dict or None
        """
        access_token = self._get_access_token()
        if not access_token:
            return None
        
        url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting subscription details: {e}")
            return None
    
    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "User requested cancellation"
    ) -> Tuple[bool, str]:
        """
        Cancel a PayPal subscription
        
        Args:
            subscription_id: PayPal subscription ID
            reason: Cancellation reason
        
        Returns:
            Tuple of (success, message)
        """
        access_token = self._get_access_token()
        if not access_token:
            return False, "Failed to authenticate with PayPal"
        
        url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "reason": reason
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Update local storage
            subscriptions = self._load_subscriptions()
            if subscription_id in subscriptions:
                subscriptions[subscription_id]["status"] = "CANCELLED"
                subscriptions[subscription_id]["cancelled_at"] = datetime.now().isoformat()
                subscriptions[subscription_id]["cancellation_reason"] = reason
                self._save_subscriptions(subscriptions)
            
            return True, "Subscription cancelled successfully"
            
        except Exception as e:
            return False, f"PayPal API error: {str(e)}"
    
    def verify_webhook_signature(
        self,
        headers: Dict,
        body: str
    ) -> bool:
        """
        Verify PayPal webhook signature
        
        Args:
            headers: Request headers
            body: Raw request body
        
        Returns:
            True if signature is valid
        """
        if not self.webhook_id:
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        url = f"{self.base_url}/v1/notifications/verify-webhook-signature"
        
        api_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
            "cert_url": headers.get("PAYPAL-CERT-URL"),
            "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
            "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
            "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
            "webhook_id": self.webhook_id,
            "webhook_event": json.loads(body)
        }
        
        try:
            response = requests.post(url, headers=api_headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("verification_status") == "SUCCESS"
        except Exception as e:
            print(f"Error verifying webhook signature: {e}")
            return False
    
    def process_webhook(self, event: Dict) -> bool:
        """
        Process PayPal webhook event
        
        Args:
            event: Webhook event data
        
        Returns:
            True if processed successfully
        """
        event_type = event.get("event_type")
        resource = event.get("resource", {})
        
        # Save webhook event
        self._save_webhook_event(event)
        
        subscriptions = self._load_subscriptions()
        subscription_id = resource.get("id")
        
        if not subscription_id or subscription_id not in subscriptions:
            # Check if it's in the resource billing agreement
            subscription_id = resource.get("billing_agreement_id")
        
        if subscription_id and subscription_id in subscriptions:
            subscription = subscriptions[subscription_id]
            
            # Update subscription status based on event type
            if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
                subscription["status"] = "ACTIVE"
                subscription["activated_at"] = datetime.now().isoformat()
            
            elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
                subscription["status"] = "CANCELLED"
                subscription["cancelled_at"] = datetime.now().isoformat()
            
            elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
                subscription["status"] = "SUSPENDED"
                subscription["suspended_at"] = datetime.now().isoformat()
            
            elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
                subscription["status"] = "EXPIRED"
                subscription["expired_at"] = datetime.now().isoformat()
            
            elif event_type == "PAYMENT.SALE.COMPLETED":
                # Record payment
                if "payments" not in subscription:
                    subscription["payments"] = []
                subscription["payments"].append({
                    "amount": resource.get("amount", {}).get("total"),
                    "currency": resource.get("amount", {}).get("currency"),
                    "timestamp": datetime.now().isoformat(),
                    "transaction_id": resource.get("id")
                })
            
            elif event_type == "PAYMENT.SALE.REFUNDED":
                subscription["status"] = "REFUNDED"
                subscription["refunded_at"] = datetime.now().isoformat()
            
            self._save_subscriptions(subscriptions)
        
        return True
    
    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """
        Get user's active subscription
        
        Args:
            user_id: User ID
        
        Returns:
            Subscription dict or None
        """
        subscriptions = self._load_subscriptions()
        
        # Find active subscription for user
        for sub_id, sub_data in subscriptions.items():
            if sub_data.get("user_id") == user_id and sub_data.get("status") == "ACTIVE":
                return sub_data
        
        return None
    
    def get_subscription_stats(self) -> Dict:
        """
        Get subscription statistics
        
        Returns:
            Stats dict with counts and revenue
        """
        subscriptions = self._load_subscriptions()
        
        stats = {
            "total_subscriptions": len(subscriptions),
            "active_subscriptions": 0,
            "cancelled_subscriptions": 0,
            "suspended_subscriptions": 0,
            "total_revenue": 0.0,
            "by_plan": {
                "pro_monthly": 0,
                "expert_monthly": 0,
                "pro_annual": 0,
                "expert_annual": 0
            }
        }
        
        for sub_data in subscriptions.values():
            status = sub_data.get("status")
            
            if status == "ACTIVE":
                stats["active_subscriptions"] += 1
            elif status == "CANCELLED":
                stats["cancelled_subscriptions"] += 1
            elif status == "SUSPENDED":
                stats["suspended_subscriptions"] += 1
            
            # Count by plan
            plan_type = sub_data.get("plan_type")
            if plan_type in stats["by_plan"]:
                stats["by_plan"][plan_type] += 1
            
            # Calculate revenue from payments
            payments = sub_data.get("payments", [])
            for payment in payments:
                amount = payment.get("amount", "0")
                try:
                    stats["total_revenue"] += float(amount)
                except:
                    pass
        
        return stats


# Singleton instance
_paypal_service = None


def get_paypal_service(sandbox_mode: bool = True) -> PayPalService:
    """
    Get PayPal service singleton instance
    
    Args:
        sandbox_mode: If True, use sandbox. If False, use production.
    
    Returns:
        PayPalService instance
    """
    global _paypal_service
    if _paypal_service is None:
        _paypal_service = PayPalService(sandbox_mode=sandbox_mode)
    return _paypal_service


# Example usage
if __name__ == "__main__":
    # This is for testing only
    service = get_paypal_service(sandbox_mode=True)
    
    # Get stats
    stats = service.get_subscription_stats()
    print("Subscription Stats:")
    print(json.dumps(stats, indent=2))
