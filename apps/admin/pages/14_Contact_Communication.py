
"""
=============================================================================
IntelliCV Admin Portal - Contact & Communication Suite (CANONICAL / BACKEND-TRUTH)
=============================================================================

Canonical control surface for:
- Contact database (CRUD) — backend truth (no local CSV writes in the UI)
- Campaign creation + delivery orchestration — backend truth
- Email provider integrations (SendGrid / Gmail / Klaviyo) — backend truth
- Email logs + analytics — backend truth
- Bulk/BCC sending — backend mediated (rate limits + consent enforcement server-side)

RULES (ENFORCED):
- NO demo/sample rows
- NO random numbers
- NO local-only fallbacks (e.g., "return True" auth, fake charts)
- NO handling of raw credentials in Streamlit UI (passwords/tokens must be stored server-side)
- Backend is the ONLY source of truth
- Missing required backend keys/endpoints -> HARD ERROR

🔴 NEW in this version (compared to your draft):
- Migrated ALL data reads/writes to Admin API endpoints (contacts, campaigns, send, logs, analytics, integrations)
- Removed hardcoded contact rows, fake performance data, and SMTP "would send" placeholders
- Added strict payload contracts (_require_dict/_require_list/_require_str)
- Added cross-link: Token Management (Page 10) -> API Integration (Page 13) remains the place for cost modelling,
  but this page can request "email cost events" from backend so token/cost accounting stays consistent
- Added "Consent & Compliance" guardrails surfaced from backend flags (GDPR / unsub / consent_required)

EXPECTED ADMIN API ENDPOINTS (add these to backend + client):
- GET    /admin/contacts
- POST   /admin/contacts
- PATCH  /admin/contacts/{contact_id}
- DELETE /admin/contacts/{contact_id}
- POST   /admin/contacts/import  (CSV upload handled by backend)
- GET    /admin/contacts/export  (returns CSV bytes or signed URL)

- GET    /admin/campaigns
- POST   /admin/campaigns
- POST   /admin/campaigns/{campaign_id}/send
- GET    /admin/campaigns/{campaign_id}

- GET    /admin/email/logs?days=30
- GET    /admin/email/analytics?days=30
- POST   /admin/email/send_bulk   (bcc + batching server-side)
- POST   /admin/email/send_test

- GET    /admin/integrations/status
- POST   /admin/integrations/sendgrid/configure
- POST   /admin/integrations/gmail/configure
- POST   /admin/integrations/klaviyo/configure
- POST   /admin/integrations/{provider}/disconnect

Notes:
- If your backend currently stores contacts in Contacts.csv, keep that internal to backend.
  The UI should never touch local files; it calls the backend which can read/write the CSV or DB.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client


# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------

st.set_page_config(page_title="Contact & Communication", page_icon="📞", layout="wide")

require_admin()
client = get_admin_api_client(access_token=get_access_token())

st.title("📞 Contact & Communication Suite")
st.caption("Backend-truth contact, campaign, sending, logs and analytics. No demo data.")

refresh = st.button("🔄 Refresh all", use_container_width=True)


# -------------------------------------------------------------------
# STRICT HELPERS
# -------------------------------------------------------------------

def _require_dict(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    v = payload.get(key)
    if not isinstance(v, dict):
        raise RuntimeError(f"Backend payload missing required dict key: '{key}'")
    return v

def _require_list(payload: Dict[str, Any], key: str) -> List[Any]:
    v = payload.get(key)
    if not isinstance(v, list):
        raise RuntimeError(f"Backend payload missing required list key: '{key}'")
    return v

def _require_str(payload: Dict[str, Any], key: str) -> str:
    v = payload.get(key)
    if not isinstance(v, str) or not v.strip():
        raise RuntimeError(f"Backend payload missing required string key: '{key}'")
    return v


# -------------------------------------------------------------------
# LOAD (CACHED; STILL BACKEND-TRUTH)
# -------------------------------------------------------------------

integrations_payload = get_cached(
    "_cc_integrations_status",
    ttl_s=30,
    fetch=client.get_integrations_status,
    force=refresh,
)

contacts_payload = get_cached(
    "_cc_contacts",
    ttl_s=30,
    fetch=client.get_contacts,
    force=refresh,
)

campaigns_payload = get_cached(
    "_cc_campaigns",
    ttl_s=30,
    fetch=client.get_campaigns,
    force=refresh,
)

analytics_payload = get_cached(
    "_cc_email_analytics",
    ttl_s=30,
    fetch=lambda: client.get_email_analytics(days=30),
    force=refresh,
)

logs_payload = get_cached(
    "_cc_email_logs",
    ttl_s=30,
    fetch=lambda: client.get_email_logs(days=30),
    force=refresh,
)


# -------------------------------------------------------------------
# TOP KPIs (BACKEND TRUTH ONLY)
# -------------------------------------------------------------------

kpis = _require_dict(analytics_payload, "kpis")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total contacts", kpis.get("total_contacts"))
c2.metric("Campaigns (30d)", kpis.get("campaigns_30d"))
c3.metric("Open rate (30d)", kpis.get("open_rate_30d"))
c4.metric("Click rate (30d)", kpis.get("click_rate_30d"))

st.markdown("---")


# -------------------------------------------------------------------
# INTEGRATIONS STATUS / CONFIG
# -------------------------------------------------------------------

with st.expander("🔗 Provider integrations", expanded=True):
    status = _require_dict(integrations_payload, "providers")  # {sendgrid:{...}, gmail:{...}, klaviyo:{...}}
    providers_df = pd.DataFrame(
        [
            {
                "provider": name,
                "connected": bool(cfg.get("connected")),
                "mode": cfg.get("mode"),
                "last_checked": cfg.get("last_checked"),
                "notes": cfg.get("notes"),
            }
            for name, cfg in status.items()
            if isinstance(cfg, dict)
        ]
    )
    st.dataframe(providers_df, use_container_width=True, hide_index=True)

    st.caption("🔴 NEW: Credentials are configured server-side via Admin API. This UI never stores raw secrets.")

    p1, p2, p3 = st.columns(3)

    with p1:
        st.subheader("SendGrid")
        sg_key = st.text_input("SendGrid API Key (server-side)", type="password", help="Stored in backend secret store.")
        if st.button("Configure SendGrid", use_container_width=True):
            if not sg_key.strip():
                st.error("SendGrid API key required.")
            else:
                res = client.configure_sendgrid(api_key=sg_key.strip())
                ok = _require_str(res, "status")
                st.success(f"✅ SendGrid configured: {ok}")
                st.rerun()

    with p2:
        st.subheader("Gmail")
        st.info("Use OAuth/service flow server-side. Avoid app-password patterns.")
        gmail_json = st.text_area(
            "Gmail OAuth JSON (server-side)",
            help="Paste credentials JSON for backend storage, or leave blank if already configured.",
            height=150,
        )
        if st.button("Configure Gmail", use_container_width=True):
            payload = {"oauth_json": gmail_json.strip() or None}
            res = client.configure_gmail(payload)
            ok = _require_str(res, "status")
            st.success(f"✅ Gmail configured: {ok}")
            st.rerun()

    with p3:
        st.subheader("Klaviyo")
        kl_key = st.text_input("Klaviyo API Key (server-side)", type="password")
        if st.button("Configure Klaviyo", use_container_width=True):
            if not kl_key.strip():
                st.error("Klaviyo API key required.")
            else:
                res = client.configure_klaviyo(api_key=kl_key.strip())
                ok = _require_str(res, "status")
                st.success(f"✅ Klaviyo configured: {ok}")
                st.rerun()

    st.markdown("#### Disconnect")
    dcol1, dcol2 = st.columns([2, 1])
    with dcol1:
        provider = st.selectbox("Provider", options=sorted(status.keys()))
    with dcol2:
        if st.button("Disconnect provider", type="secondary", use_container_width=True):
            res = client.disconnect_integration(provider)
            ok = _require_str(res, "status")
            st.success(f"✅ Disconnected: {ok}")
            st.rerun()


# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    ["👥 Contacts", "📧 Campaigns", "📮 Send (bulk/BCC)", "📊 Logs & analytics"]
)


# -------------------------------------------------------------------
# CONTACTS
# -------------------------------------------------------------------

with tab1:
    st.subheader("👥 Contact database (backend truth)")

    contacts = _require_list(contacts_payload, "contacts")  # list[contact]
    if contacts:
        st.dataframe(pd.DataFrame(contacts), use_container_width=True, hide_index=True)
    else:
        st.info("No contacts returned by backend. (Real zero)")

    st.markdown("### ➕ Add contact")
    with st.form("cc_add_contact"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        company = st.text_input("Company")
        role = st.text_input("Role")
        tags = st.text_input("Tags (comma-separated)")
        consent = st.checkbox("Consent captured", value=False, help="Backend may enforce consent_required=True.")
        app_offer = st.checkbox("Eligible for app offers", value=False)

        submitted = st.form_submit_button("Add contact")

    if submitted:
        payload = {
            "name": name.strip() or None,
            "email": email.strip(),
            "company": company.strip() or None,
            "role": role.strip() or None,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "consent": bool(consent),
            "app_offer_eligible": bool(app_offer),
        }
        res = client.create_contact(payload)
        saved = _require_dict(res, "contact")
        st.success(f"✅ Contact created: {saved.get('email')}")
        st.rerun()

    st.markdown("### 📥 Import contacts")
    st.caption("🔴 NEW: CSV import is handled by backend (/admin/contacts/import).")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up is not None and st.button("Import CSV to backend", use_container_width=True):
        data = up.getvalue()
        res = client.import_contacts_csv(filename=up.name, content_bytes=data)
        st.success(f"✅ Imported: {res.get('imported')} | Updated: {res.get('updated')} | Skipped: {res.get('skipped')}")
        st.rerun()

    st.markdown("### 📤 Export contacts")
    if st.button("Export CSV", use_container_width=True):
        export = client.export_contacts_csv()
        # Contract: {filename, content_base64} OR {url}
        if "url" in export:
            st.success("✅ Export prepared (signed URL).")
            st.write(export["url"])
        else:
            filename = _require_str(export, "filename")
            content_b64 = _require_str(export, "content_base64")
            import base64
            st.download_button(
                "Download CSV",
                data=base64.b64decode(content_b64),
                file_name=filename,
                mime="text/csv",
                use_container_width=True,
            )


# -------------------------------------------------------------------
# CAMPAIGNS
# -------------------------------------------------------------------

with tab2:
    st.subheader("📧 Campaigns (backend truth)")

    campaigns = _require_list(campaigns_payload, "campaigns")
    if campaigns:
        st.dataframe(pd.DataFrame(campaigns), use_container_width=True, hide_index=True)
    else:
        st.info("No campaigns returned by backend. (Real zero)")

    st.markdown("### ➕ Create campaign")
    with st.form("cc_create_campaign"):
        name = st.text_input("Campaign name")
        subject = st.text_input("Subject")
        template_id = st.text_input("Template ID (optional)", help="Backend resolves templates; UI doesn't embed bodies.")
        audience = st.multiselect(
            "Audience tags",
            options=sorted(list(set(sum([c.get("tags", []) for c in contacts if isinstance(c, dict)], [])))),
            help="Backend will resolve recipients by tags + consent + suppression lists.",
        )
        app_offer_only = st.checkbox("Only app-offer eligible contacts", value=False)
        send_now = st.checkbox("Send now", value=False)
        submitted = st.form_submit_button("Create campaign")

    if submitted:
        payload = {
            "name": name.strip(),
            "subject": subject.strip(),
            "template_id": template_id.strip() or None,
            "audience_tags": audience,
            "app_offer_only": bool(app_offer_only),
        }
        created = client.create_campaign(payload)
        camp = _require_dict(created, "campaign")
        st.success(f"✅ Campaign created: {camp.get('name')}")
        if send_now:
            res = client.send_campaign(camp.get("id"))
            st.success(f"📤 Send started: {res.get('status')}")
        st.rerun()

    st.markdown("### 📤 Send an existing campaign")
    if campaigns:
        id_map = {f"{c.get('name','(unnamed)')} — {c.get('id','')}": c.get("id") for c in campaigns if isinstance(c, dict)}
        choice = st.selectbox("Campaign", options=list(id_map.keys()))
        if st.button("Send selected campaign", type="primary", use_container_width=True):
            cid = id_map[choice]
            res = client.send_campaign(cid)
            st.success(f"📤 Send started: {res.get('status')}")
            st.rerun()


# -------------------------------------------------------------------
# BULK / BCC SEND
# -------------------------------------------------------------------

with tab3:
    st.subheader("📮 Bulk/BCC send (backend mediated)")
    st.caption("🔴 NEW: Batching, rate limits, suppression, unsubscribe, and consent enforcement happen in backend.")

    mode = st.radio("Mode", options=["Test send", "Bulk/BCC send"], horizontal=True)

    if mode == "Test send":
        with st.form("cc_test_send"):
            to = st.text_input("To (email)")
            subject = st.text_input("Subject", key="cc_test_subject")
            body = st.text_area("Body", height=180)
            provider = st.selectbox("Provider", options=["sendgrid", "gmail"])
            submit = st.form_submit_button("Send test email")
        if submit:
            res = client.send_test_email({"to": to.strip(), "subject": subject.strip(), "body": body, "provider": provider})
            st.success(f"✅ Test send queued: {res.get('status')}")
    else:
        with st.form("cc_bulk_send"):
            subject = st.text_input("Subject", key="cc_bulk_subject")
            body = st.text_area("Body", height=180, help="Backend may enforce template usage; this is allowed for now.")
            audience_tag = st.text_input("Audience tag", help="Backend resolves recipients by tag.")
            batch_size = st.number_input("Batch size", min_value=1, max_value=500, value=50, step=1)
            delay_seconds = st.number_input("Delay between batches (seconds)", min_value=0, max_value=300, value=10, step=1)
            provider = st.selectbox("Provider", options=["sendgrid", "gmail"], key="cc_bulk_provider")
            submit = st.form_submit_button("Start bulk/BCC send", type="primary")

        if submit:
            payload = {
                "subject": subject.strip(),
                "body": body,
                "audience_tag": audience_tag.strip(),
                "batch_size": int(batch_size),
                "delay_seconds": int(delay_seconds),
                "provider": provider,
            }
            res = client.send_bulk_email(payload)
            st.success(f"📤 Bulk send started: {res.get('status')} (job_id={res.get('job_id')})")


# -------------------------------------------------------------------
# LOGS & ANALYTICS
# -------------------------------------------------------------------

with tab4:
    st.subheader("📊 Email logs (backend truth)")

    logs = _require_list(logs_payload, "logs")
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("Backend returned 0 log rows for this period. (Real zero)")

    st.markdown("---")
    st.subheader("📈 Analytics (30 days)")

    series = _require_list(analytics_payload, "timeseries")  # list[{date,sent,delivered,opens,clicks,bounces}]
    if series:
        df = pd.DataFrame(series)
        if "date" not in df.columns:
            raise RuntimeError("Analytics timeseries requires key: date")
        idx = df.set_index("date")
        for col in ["sent", "delivered", "opens", "clicks", "bounces"]:
            if col in idx.columns:
                st.line_chart(idx[[col]])
    else:
        st.info("Backend returned empty timeseries. This is a real zero OR analytics not wired yet.")

    st.markdown("---")
    st.subheader("🧾 Compliance flags")
    compliance = _require_dict(integrations_payload, "compliance")  # {consent_required, unsubscribe_enabled, ...}
    st.json(compliance)
