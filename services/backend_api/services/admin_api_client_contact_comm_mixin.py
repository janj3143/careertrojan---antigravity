
"""services.admin_api_client — PATCH: Contact & Communication endpoints

Drop these methods into your existing services/admin_api_client.py (or merge).
They assume your client already has a _request(method, path, json=None, files=None, params=None) helper.

🔴 NEW: Contact & Communication Suite endpoints.
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class AdminAPIClientContactCommunicationMixin:
    # ---------------------------
    # Integrations
    # ---------------------------
    def get_integrations_status(self) -> Dict[str, Any]:
        return self._request("GET", "/admin/integrations/status")

    def configure_sendgrid(self, api_key: str) -> Dict[str, Any]:
        return self._request("POST", "/admin/integrations/sendgrid/configure", json={"api_key": api_key})

    def configure_gmail(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/admin/integrations/gmail/configure", json=payload)

    def configure_klaviyo(self, api_key: str) -> Dict[str, Any]:
        return self._request("POST", "/admin/integrations/klaviyo/configure", json={"api_key": api_key})

    def disconnect_integration(self, provider: str) -> Dict[str, Any]:
        return self._request("POST", f"/admin/integrations/{provider}/disconnect")

    # ---------------------------
    # Contacts
    # ---------------------------
    def get_contacts(self) -> Dict[str, Any]:
        return self._request("GET", "/admin/contacts")

    def create_contact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/admin/contacts", json=payload)

    def update_contact(self, contact_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/admin/contacts/{contact_id}", json=payload)

    def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/admin/contacts/{contact_id}")

    def import_contacts_csv(self, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        # expects multipart/form-data {file}
        files = {"file": (filename, content_bytes, "text/csv")}
        return self._request("POST", "/admin/contacts/import", files=files)

    def export_contacts_csv(self) -> Dict[str, Any]:
        # backend can return {url} OR {filename, content_base64}
        return self._request("GET", "/admin/contacts/export")

    # ---------------------------
    # Campaigns
    # ---------------------------
    def get_campaigns(self) -> Dict[str, Any]:
        return self._request("GET", "/admin/campaigns")

    def create_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/admin/campaigns", json=payload)

    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/admin/campaigns/{campaign_id}/send")

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/admin/campaigns/{campaign_id}")

    # ---------------------------
    # Email send / logs / analytics
    # ---------------------------
    def send_test_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/admin/email/send_test", json=payload)

    def send_bulk_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/admin/email/send_bulk", json=payload)

    def get_email_logs(self, days: int = 30) -> Dict[str, Any]:
        return self._request("GET", "/admin/email/logs", params={"days": int(days)})

    def get_email_analytics(self, days: int = 30) -> Dict[str, Any]:
        return self._request("GET", "/admin/email/analytics", params={"days": int(days)})
