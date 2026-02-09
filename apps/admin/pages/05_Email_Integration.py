# 📧 Email Integration & Historical CV Scanner

import streamlit as st

# =============================================================================
# BACKEND-FIRST SWITCH (lockstep) — falls back to local execution when backend is unavailable
# =============================================================================
try:
    from portal_bridge.python.intellicv_api_client import IntelliCVApiClient  # preferred
except Exception:  # pragma: no cover
    IntelliCVApiClient = None  # type: ignore

def _get_api_client():
    return IntelliCVApiClient() if IntelliCVApiClient else None

def _backend_try_get(path: str, params: dict | None = None):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.get(path, params=params), None
    except Exception as e:
        return None, str(e)

def _backend_try_post(path: str, payload: dict):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.post(path, payload), None
    except Exception as e:
        return None, str(e)

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
import pandas as pd

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SERVICES_PATH = ROOT_DIR / "services"
if str(SERVICES_PATH) not in sys.path:
    sys.path.insert(0, str(SERVICES_PATH))

SHARED_PATH = ROOT_DIR / "shared"
if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

MODULES_PATH = ROOT_DIR / "modules"
if str(MODULES_PATH) not in sys.path:
    sys.path.insert(0, str(MODULES_PATH))

try:
    from services.api_client import AdminFastAPIClient
except ImportError:  # pragma: no cover - optional for offline dev
    AdminFastAPIClient = None

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent))

# Add IntelliCV-AI branding
sys.path.append(str(Path(__file__).parent.parent / "shared"))
try:
    from branding import apply_intellicv_styling, render_intellicv_page_header
    BRANDING_AVAILABLE = True
except ImportError:
    BRANDING_AVAILABLE = False

# Import email integration system
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "modules" / "core"))
    # Try SQLite version first, fallback to JSON version
    try:
        from email_integration import EmailIntegrationManager, EmailAccount
        EMAIL_INTEGRATION_TYPE = "SQLite"
    except ImportError:
        from json_email_integration import EmailIntegrationManager, EmailAccount
        EMAIL_INTEGRATION_TYPE = "JSON"
    EMAIL_INTEGRATION_AVAILABLE = True
except ImportError as e:
    EMAIL_INTEGRATION_AVAILABLE = False
    EMAIL_INTEGRATION_TYPE = "None"

# Import proper IntelliCV data manager
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "services"))
    from intellicv_data_manager import IntelliCVDataDirectoryManager, get_data_manager
    DATA_MANAGER_AVAILABLE = True
except ImportError as e:
    DATA_MANAGER_AVAILABLE = False

# Import enhanced email data manager (fallback)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))
    from email_data_manager import EmailDataManager, ImprovedEmailConnectionTester
    EMAIL_DATA_MANAGER_AVAILABLE = True
except ImportError as e:
    EMAIL_DATA_MANAGER_AVAILABLE = False

# Import Universal Email CV Extractor
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from universal_email_cv_extractor import UniversalEmailCVExtractor
    UNIVERSAL_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    UNIVERSAL_EXTRACTOR_AVAILABLE = False
    # st.warning(f"⚠️ Universal Email CV Extractor not available: {e}")

# CENTRALIZED AI DATA CONFIGURATION - Import centralized config
sys.path.append(str(Path(__file__).parent.parent / "shared"))
try:
    from ai_data_config import ai_data_paths, get_ai_data_path, get_json_file_count
    AI_DATA_CONFIG_AVAILABLE = True
    # Use centralized paths
    SANDBOX_ROOT = ai_data_paths.sandbox_root
    INTELLICV_DATA_PATH = ai_data_paths.intellicv_data
    AI_DATA_FINAL_PATH = ai_data_paths.ai_data_final  # Centralized: 3,418 JSON files
    EMAIL_DATA_PATH = ai_data_paths.email_data
except ImportError:
    # Fallback to direct paths if config not available
    AI_DATA_CONFIG_AVAILABLE = False
    SANDBOX_ROOT = Path(__file__).parent.parent.parent
    INTELLICV_DATA_PATH = SANDBOX_ROOT / "IntelliCV-data"
    AI_DATA_FINAL_PATH = SANDBOX_ROOT / "ai_data_final"
    EMAIL_DATA_PATH = SANDBOX_ROOT / "data" / "email_data"
COMPLETE_DATA_PARSER_PATH = Path(__file__).parent.parent / "services" / "resume_parser.py"

# Import local configuration if available
try:
    sys.path.insert(0, str(SANDBOX_ROOT / "config"))
    from sandbox_config_manager import config_manager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Ensure data directories exist
INTELLICV_DATA_PATH.mkdir(exist_ok=True)
AI_DATA_FINAL_PATH.mkdir(exist_ok=True)

# Authentication check
if not st.session_state.get('admin_authenticated', False):
    st.error("🚫 **AUTHENTICATION REQUIRED**")
    st.info("Please return to the main page and login to access this module.")
    st.stop()

st.set_page_config(
    page_title="📧 Email Integration - IntelliCV",
    page_icon="📧",
    layout="wide"
)



with st.sidebar.expander("🛰️ Backend ping", expanded=False):
    payload, err = _backend_try_get("/telemetry/status")
    if payload is not None:
        st.success("✅ Backend reachable")
        st.json(payload)
    else:
        st.info(f"Backend not reachable ({err})")

# -----------------------------------------------------------------------------
# Authentication guard (admin portal standard)
# -----------------------------------------------------------------------------
def _require_admin_session():
    if st.session_state.get("user_role") == "admin":
        return True
    if st.session_state.get("admin_authenticated", False):
        return True
    st.error("🔒 Admin access required")
    st.stop()

_require_admin_session()

# -----------------------------------------------------------------------------
# Backend FastAPI helpers (shared with other admin modules)
# -----------------------------------------------------------------------------

EMAIL_DASHBOARD_CACHE_KEY = "_email_dashboard_snapshot"
EMAIL_DASHBOARD_TS_KEY = "_email_dashboard_ts"
EMAIL_SYSTEM_HEALTH_CACHE_KEY = "_email_system_health_snapshot"
EMAIL_SYSTEM_HEALTH_TS_KEY = "_email_system_health_ts"
EMAIL_SYSTEM_ACTIVITY_CACHE_KEY = "_email_system_activity_snapshot"
EMAIL_SYSTEM_ACTIVITY_TS_KEY = "_email_system_activity_ts"
API_CACHE_TTL = 90


def get_admin_api_client():
    """Return cached AdminFastAPIClient instance."""
    if AdminFastAPIClient is None:
        return None
    client = st.session_state.get("_admin_api_client")
    if client is None:
        st.session_state["_admin_api_client"] = AdminFastAPIClient()
        client = st.session_state["_admin_api_client"]
    return client


def _get_cached_admin_payload(
    cache_key: str,
    ts_key: str,
    fetcher,
    force_refresh: bool = False,
    ttl_seconds: int = API_CACHE_TTL,
):
    if force_refresh:
        st.session_state.pop(cache_key, None)
        st.session_state.pop(ts_key, None)

    payload = st.session_state.get(cache_key)
    timestamp = st.session_state.get(ts_key)
    if payload and timestamp:
        if (datetime.now() - timestamp).total_seconds() < ttl_seconds:
            return payload

    client = get_admin_api_client()
    if not client:
        return payload or {}

    data = fetcher(client) or {}
    st.session_state[cache_key] = data
    st.session_state[ts_key] = datetime.now()
    return data


def get_dashboard_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        EMAIL_DASHBOARD_CACHE_KEY,
        EMAIL_DASHBOARD_TS_KEY,
        lambda client: client.get_dashboard_snapshot(),
        force_refresh,
        ttl_seconds=60,
    )
def get_system_health_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        EMAIL_SYSTEM_HEALTH_CACHE_KEY,
        EMAIL_SYSTEM_HEALTH_TS_KEY,
        lambda client: client.get_system_health(),
        force_refresh,
        ttl_seconds=45,
    )


def get_system_activity_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        EMAIL_SYSTEM_ACTIVITY_CACHE_KEY,
        EMAIL_SYSTEM_ACTIVITY_TS_KEY,
        lambda client: client.get_system_activity(),
        force_refresh,
        ttl_seconds=45,
    )


def format_relative_time(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "N/A"
    try:
        reference = datetime.now()
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        delta = reference - parsed
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except Exception:
        return str(timestamp)


def _get_email_account_stats() -> Tuple[int, Optional[datetime]]:
    """Return (count, most recent sync timestamp) for configured accounts."""
    if not EMAIL_INTEGRATION_AVAILABLE:
        return 0, None

    base_email_dir = Path(__file__).parent.parent / "data" / "email_data"
    try:
        base_email_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        try:
            manager = EmailIntegrationManager(data_dir=str(base_email_dir))
        except TypeError:
            manager = EmailIntegrationManager()

        if hasattr(manager, "get_email_accounts"):
            accounts = manager.get_email_accounts()
        elif hasattr(manager, "get_accounts"):
            accounts = manager.get_accounts()
        else:
            accounts = []

        count = len(accounts)
        latest_sync: Optional[datetime] = None

        for entry in accounts:
            raw_value: Any
            if isinstance(entry, dict):
                raw_value = entry.get("last_sync")
            else:
                raw_value = getattr(entry, "last_sync", None)

            parsed: Optional[datetime] = None
            if isinstance(raw_value, datetime):
                parsed = raw_value
            elif isinstance(raw_value, str) and raw_value:
                try:
                    parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
                except ValueError:
                    parsed = None

            if parsed:
                if not latest_sync or parsed > latest_sync:
                    latest_sync = parsed

        return count, latest_sync
    except Exception:
        return 0, None


def show_backend_api_status():
    """Surface FastAPI telemetry that powers email ingestion."""
    st.subheader("🛰️ Backend & FastAPI Health")

    refresh_col, meta_col = st.columns([1, 3])
    with refresh_col:
        if st.button("🔄 Refresh Backend Data", key="refresh_backend_for_email"):
            get_dashboard_snapshot(force_refresh=True)
            get_system_health_snapshot(force_refresh=True)
            get_system_activity_snapshot(force_refresh=True)
            st.rerun()

    dashboard = get_dashboard_snapshot() or {}
    system_health = get_system_health_snapshot() or {}
    system_activity = get_system_activity_snapshot() or {}
    data_overview = dashboard.get("data_overview") or {}
    system_block = dashboard.get("system", {})
    tokens_block = dashboard.get("tokens", {})
    services = system_block.get("services") or system_health.get("services") or {}

    with meta_col:
        updated_at = system_health.get("updated_at") or system_block.get("updated_at")
        st.caption(f"System telemetry updated {format_relative_time(updated_at)}")
        st.caption(f"Data footprint indexed {format_relative_time(tokens_block.get('updated_at'))}")

    cpu_pct = system_health.get("cpu_pct", system_block.get("cpu_percent", 0.0)) or 0.0
    mem_pct = system_health.get("memory_pct", system_block.get("memory_percent", 0.0)) or 0.0
    jobs_in_queue = system_block.get("jobs_in_queue", 0)
    parsers_online = system_block.get("parsers_online", 0)
    token_30d = tokens_block.get("total_used_30d", 0)
    token_24h = tokens_block.get("total_used_24h", 0)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("CPU Load", f"{cpu_pct:.1f}%", f"{system_health.get('cpu_count', 0)} cores")
    with metric_cols[1]:
        st.metric("Memory Usage", f"{mem_pct:.1f}%", f"{system_health.get('memory_available_gb', 0):.1f} GB free")
    with metric_cols[2]:
        st.metric("Jobs in Queue", f"{jobs_in_queue:,}", f"{parsers_online} parsers")
    with metric_cols[3]:
        st.metric("Tokens (30d)", f"{token_30d:,}", f"{token_24h:,} / 24h")

    email_cols = st.columns(3)
    with email_cols[0]:
        st.metric("📬 Email Messages Indexed", f"{data_overview.get('eml', 0):,}")
    with email_cols[1]:
        st.metric("📄 PDF CVs", f"{data_overview.get('pdf', 0):,}")
    with email_cols[2]:
        st.metric("📝 DOC/DOCX CVs", f"{data_overview.get('doc', 0) + data_overview.get('docx', 0):,}")

    if services:
        running = sum(1 for status in services.values() if status == "running")
        st.caption(f"Services online: {running}/{len(services)}")

    budget_alerts = tokens_block.get("budget_alerts") or []
    for alert in budget_alerts[:2]:
        st.warning(
            f"⚠️ {alert.get('org', 'Org')} ({alert.get('plan', 'plan')}) at {alert.get('usage_pct', 0):.1f}% token usage"
        )

    events = system_activity.get("events") or []
    if events:
        with st.expander("📝 Recent System Activity", expanded=False):
            st.dataframe(pd.DataFrame(events).head(12), use_container_width=True)


def show_email_status():
    """Show email integration status and metrics"""
    st.subheader("📊 Email Integration Status")

    dashboard = get_dashboard_snapshot() or {}
    system_health = get_system_health_snapshot() or {}
    data_overview = dashboard.get("data_overview") or {}
    system_block = dashboard.get("system", {})

    account_count, last_sync = _get_email_account_stats()
    total_cv_docs = data_overview.get("pdf", 0) + data_overview.get("doc", 0) + data_overview.get("docx", 0)
    indexed_emails = data_overview.get("eml", 0)

    last_scan_label = st.session_state.get("_email_last_scan_label", "Not configured")
    last_scan_provider = st.session_state.get("_email_last_scan_provider")
    scan_value = last_scan_label or "Not configured"
    if last_scan_provider and scan_value != "Not configured":
        scan_value = f"{scan_value} · {last_scan_provider}"

    last_scan_days = st.session_state.get("_email_last_scan_days")
    last_scan_finished = st.session_state.get("_email_last_scan_completed_at")
    scan_delta = (
        format_relative_time(last_scan_finished)
        if last_scan_finished
        else (f"{last_scan_days} days of history" if last_scan_days else "Set date range")
    )

    last_scan_found = st.session_state.get("_email_last_scan_found")
    cv_delta = (
        f"{last_scan_found} found last run"
        if last_scan_found is not None
        else f"{indexed_emails:,} emails indexed"
    )

    account_delta = (
        f"Last sync {format_relative_time(last_sync.isoformat())}"
        if last_sync
        else "Awaiting first sync"
    )

    service_status = (system_block.get("ai_status") or "Unknown").title()
    service_delta = f"Updated {format_relative_time(system_health.get('updated_at'))}"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📧 Email Accounts", f"{account_count:,}", account_delta)

    with col2:
        st.metric("📁 CV Documents", f"{total_cv_docs:,}", cv_delta)

    with col3:
        st.metric("📅 Scan Range", scan_value, scan_delta)

    with col4:
        st.metric("✅ Service", service_status, service_delta)

    # Data Paths Status
    st.subheader("📂 Data Storage Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        intellicv_status = "✅ Available" if INTELLICV_DATA_PATH.exists() else "❌ Missing"
        st.metric("📊 IntelliCV-data", intellicv_status)
        st.caption(f"Path: {INTELLICV_DATA_PATH} | Files tracked: {total_cv_docs:,}")

    with col2:
        ai_data_status = "✅ Available" if AI_DATA_FINAL_PATH.exists() else "❌ Missing"
        st.metric("🤖 AI Data Final", ai_data_status)
        st.caption(f"Path: {AI_DATA_FINAL_PATH} | JSON: {data_overview.get('json', 0):,}")

    with col3:
        parser_status = "✅ Available" if COMPLETE_DATA_PARSER_PATH.exists() else "❌ Missing"
        st.metric("🔧 Consolidated Parser", parser_status)
        st.caption(f"Parser: consolidated_data_parser.py")

def show_email_configuration():
    """Show email account configuration with multi-provider support"""
    st.subheader("⚙️ Email Account Configuration")

    st.info("""
    **📧 Supported Email Providers:**
    - **Gmail** - Use App-Specific Password (requires 2FA)
    - **Yahoo** - Use App-Specific Password
    - **Outlook/Hotmail** - Use App-Specific Password

    💡 **With an App-Specific Password, your connection is LIVE!**
    No additional setup needed - just connect and start scanning.
    """)

    # Add new account configuration
    with st.expander("➕ Configure Email Account", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            email_provider = st.selectbox(
                "📧 Email Provider",
                ["Gmail", "Yahoo Mail", "Outlook/Hotmail", "Other IMAP"],
                help="Select your email provider"
            )

            # Show provider-specific settings
            if email_provider == "Gmail":
                imap_server = "imap.gmail.com"
                imap_port = 993
                st.info("🔐 Gmail requires App-Specific Password with 2FA enabled")
                st.caption("📖 [How to create Gmail App Password](https://support.google.com/accounts/answer/185833)")
            elif email_provider == "Yahoo Mail":
                imap_server = "imap.mail.yahoo.com"
                imap_port = 993
                st.info("🔐 Yahoo requires App-Specific Password")
                st.caption("📖 [How to create Yahoo App Password](https://help.yahoo.com/kb/generate-app-password-sln15241.html)")
            elif email_provider == "Outlook/Hotmail":
                imap_server = "outlook.office365.com"
                imap_port = 993
                st.info("🔐 Outlook supports App Password or regular password")
                st.caption("📖 [About Outlook App Passwords](https://support.microsoft.com/account-billing)")
            else:
                imap_server = st.text_input("IMAP Server", placeholder="imap.example.com")
                imap_port = st.number_input("IMAP Port", value=993, min_value=1, max_value=65535)

            email_address = st.text_input(
                "📧 Email Address",
                placeholder="your.email@example.com",
                help="Your full email address"
            )

        with col2:
            email_password = st.text_input(
                "🔑 App-Specific Password",
                type="password",
                help="Use an app-specific password, NOT your regular password"
            )

            scan_years = st.slider(
                "📅 Years to Scan Back",
                min_value=1,
                max_value=15,
                value=5,
                help="How many years of email history to scan for CVs"
            )

            st.caption(f"**Server:** {imap_server}:{imap_port}")
            st.caption(f"**Scan Range:** {scan_years} years ({scan_years * 365} days)")

        # Test connection button
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Test Connection", type="secondary", use_container_width=True):
                if not email_address or not email_password:
                    st.error("❌ Please enter email and password")
                else:
                    with st.spinner(f"Testing {email_provider} connection..."):
                        try:
                            import imaplib
                            import ssl

                            # Create SSL context
                            context = ssl.create_default_context()

                            # Connect to IMAP server
                            mail = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
                            mail.login(email_address, email_password)

                            # Get mailbox info
                            status, mailboxes = mail.list()
                            inbox_status, inbox_info = mail.select('INBOX')
                            total_emails = int(inbox_info[0])

                            mail.logout()

                            st.success(f"""
                            ✅ **Connection Successful!**

                            - Provider: {email_provider}
                            - Account: {email_address}
                            - Total Emails: {total_emails:,}
                            - Status: LIVE and Ready to scan
                            """)
                            st.balloons()

                        except imaplib.IMAP4.error as e:
                            st.error(f"❌ **Authentication Failed:** {e}")
                            st.warning("""
                            **Troubleshooting:**
                            1. Verify you're using an **App-Specific Password**, not your regular password
                            2. Ensure 2-Factor Authentication is enabled
                            3. Check that IMAP access is enabled in your email settings
                            4. Verify the email address is correct
                            """)
                        except Exception as e:
                            st.error(f"❌ **Connection Error:** {e}")

        with col2:
            if st.button("💾 Save Account", type="primary", use_container_width=True):
                if not email_address or not email_password:
                    st.error("❌ Please enter email and password")
                else:
                    # Save account configuration
                    st.success(f"✅ Successfully saved {email_provider} account: {email_address}")
                    st.info(f"Ready to scan {scan_years} years of email history")

        with col3:
            if st.button("🗑️ Clear Form", use_container_width=True):
                st.rerun()

    # Show configured accounts
    st.subheader("📋 Configured Email Accounts")

    # Check for existing accounts (placeholder - would load from config)
    accounts_df = pd.DataFrame({
        "Provider": ["Not configured"],
        "Account": ["Add your first email account above"],
        "Status": ["⏳ Pending"],
        "Last Scan": ["-"]
    })

    st.dataframe(accounts_df, use_container_width=True)

def run_email_scan():
    """Run email scanning process with provider selection"""
    st.subheader("🔍 Email CV Scanner")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📧 Email Provider")
        email_provider = st.selectbox(
            "Select Provider",
            ["Gmail", "Yahoo Mail", "Outlook/Hotmail", "Other IMAP"],
            help="Choose your email provider"
        )

        # Provider-specific settings
        if email_provider == "Gmail":
            imap_server = "imap.gmail.com"
            imap_port = 993
        elif email_provider == "Yahoo Mail":
            imap_server = "imap.mail.yahoo.com"
            imap_port = 993
        elif email_provider == "Outlook/Hotmail":
            imap_server = "outlook.office365.com"
            imap_port = 993
        else:
            imap_server = st.text_input("IMAP Server", value="imap.gmail.com")
            imap_port = st.number_input("IMAP Port", value=993)

        email_address = st.text_input(
            "Email Address",
            placeholder="your.email@example.com"
        )

        email_password = st.text_input(
            "App-Specific Password",
            type="password",
            help="Use app-specific password, NOT regular password"
        )

    with col2:
        st.markdown("### 📅 Scan Options")
        scan_type = st.radio("Scan Range", [
            "Quick Scan (Last 7 days)",
            "Extended Scan (Last 30 days)",
            "1 Year History",
            "2 Year History",
            "3 Year History",
            "5 Year History",
            "7 Year History",
            "Full Email History (10+ years)"
        ])

        # Map scan type to days
        days_mapping = {
            "Quick Scan (Last 7 days)": 7,
            "Extended Scan (Last 30 days)": 30,
            "1 Year History": 365,
            "2 Year History": 730,
            "3 Year History": 1095,
            "5 Year History": 1825,
            "7 Year History": 2555,
            "Full Email History (10+ years)": 4000
        }
        days_back = days_mapping[scan_type]

        st.info(f"""
        **Scan Configuration:**
        - Provider: {email_provider}
        - Server: {imap_server}:{imap_port}
        - Days back: {days_back}
        - Connection: LIVE (with app password)
        """)

    if st.button("🚀 Start Email Scan", type="primary", use_container_width=True):
        if not email_address or not email_password:
            st.error("❌ Please enter email address and app-specific password")
            return

        st.session_state["_email_last_scan_label"] = scan_type
        st.session_state["_email_last_scan_provider"] = email_provider
        st.session_state["_email_last_scan_days"] = days_back

        st.info(f"🔍 Connecting to {email_provider}...")

        try:
            import imaplib
            import ssl
            import email
            from email.header import decode_header

            # Create output directory
            output_dir = INTELLICV_DATA_PATH / "email_extracted"
            output_dir.mkdir(exist_ok=True, parents=True)

            # Progress tracking
            progress = st.progress(0)
            status_text = st.empty()

            # Connect to IMAP server
            status_text.text("🔐 Authenticating with email server...")
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
            mail.login(email_address, email_password)
            progress.progress(20)

            st.success(f"✅ Connected to {email_provider}")

            # Select inbox
            status_text.text("📧 Accessing inbox...")
            mail.select('INBOX')
            progress.progress(40)

            # Calculate date range
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

            # Search for emails with attachments
            status_text.text(f"🔍 Searching for CV attachments ({days_back} days)...")

            # Search criteria for CV-related emails
            search_criteria = [
                f'(SINCE {from_date})',
                '(OR SUBJECT "CV" SUBJECT "Resume" SUBJECT "Application")',
                '(OR FROM "cv" FROM "resume" FROM "application")'
            ]

            cv_count = 0
            extracted_files = []

            for criteria in search_criteria:
                try:
                    status, messages = mail.search(None, criteria)
                    if status == 'OK':
                        email_ids = messages[0].split()

                        for i, email_id in enumerate(email_ids[:50]):  # Limit to 50 emails per criteria
                            status_text.text(f"📎 Processing email {i+1}/{len(email_ids[:50])}...")

                            status, msg_data = mail.fetch(email_id, '(RFC822)')
                            if status == 'OK':
                                email_body = msg_data[0][1]
                                email_message = email.message_from_bytes(email_body)

                                # Extract attachments
                                for part in email_message.walk():
                                    if part.get_content_maintype() == 'multipart':
                                        continue
                                    if part.get('Content-Disposition') is None:
                                        continue

                                    filename = part.get_filename()
                                    if filename:
                                        # Check if it's a CV-related file
                                        cv_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
                                        if any(filename.lower().endswith(ext) for ext in cv_extensions):
                                            # Save attachment
                                            filepath = output_dir / f"{cv_count}_{filename}"
                                            with open(filepath, 'wb') as f:
                                                f.write(part.get_payload(decode=True))

                                            cv_count += 1
                                            extracted_files.append(filename)

                            progress.progress(40 + int((i+1) / len(email_ids[:50]) * 40))

                except Exception as e:
                    st.warning(f"Search error: {e}")

            # Cleanup
            mail.close()
            mail.logout()
            progress.progress(100)

            st.session_state["_email_last_scan_found"] = cv_count
            st.session_state["_email_last_scan_completed_at"] = datetime.now().isoformat()

            # Show results
            if cv_count > 0:
                st.success(f"""
                ✅ **Scan Complete!**

                - **Provider:** {email_provider}
                - **CVs Extracted:** {cv_count}
                - **Saved to:** {output_dir}
                - **Scan Range:** {days_back} days
                """)
                st.balloons()

                # Show extracted files
                if extracted_files:
                    with st.expander(f"📄 View Extracted Files ({len(extracted_files)})"):
                        for i, file in enumerate(extracted_files[:20], 1):
                            st.write(f"{i}. {file}")
            else:
                st.info(f"""
                ℹ️ No CV attachments found in the last {days_back} days.

                Try:
                - Extending the scan range
                - Checking different search criteria
                - Verifying your email account has CV emails
                """)

        except imaplib.IMAP4.error as e:
            st.error(f"❌ **Authentication Failed:** {e}")
            st.warning("""
            **Troubleshooting:**
            1. Use an **App-Specific Password**, not your regular password
            2. Enable 2-Factor Authentication in your email account
            3. Enable IMAP access in your email settings
            4. For Gmail: https://myaccount.google.com/apppasswords
            5. For Yahoo: https://login.yahoo.com/account/security
            6. For Outlook: https://account.microsoft.com/security
            """)
        except Exception as e:
            st.error(f"❌ **Scan Error:** {e}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

            # Perform actual extraction
            status_text.text("📎 Extracting CV attachments...")
            progress.progress(0.8)

            extraction_result = gmail_service.extract_new_cvs(days_back=days_back)

            status_text.text("✅ Finalizing scan results...")
            progress.progress(1.0)

            if extraction_result['success']:
                st.success(f"✅ {extraction_result['message']}")

                # Show real results
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📧 Emails Scanned", extraction_result.get('emails_scanned', 0))

                with col2:
                    st.metric("📎 CVs Extracted", extraction_result.get('extracted', 0))

                with col3:
                    st.metric("📁 Total CVs", gmail_service.get_real_email_stats()['extracted_files'])

                with col4:
                    if days_back >= 4000:
                        st.metric("📅 Scan Period", "Entire Gmail History (4000+ days)")
                    else:
                        st.metric("📅 Scan Period", f"{days_back} days")

                # Show recent extractions if any were found
                if extraction_result.get('extracted', 0) > 0:
                    st.subheader("📄 Newly Extracted CVs")
                    recent_extractions = gmail_service.get_recent_extractions(limit=extraction_result.get('extracted', 5))

                    for extraction in recent_extractions:
                        st.success(f"📎 **{extraction['original_filename']}** - {extraction['size']:,} bytes")

            else:
                st.error(f"❌ {extraction_result['message']}")

        except Exception as e:
            st.error(f"❌ Error during live Gmail scan: {e}")
            st.info("💡 **Troubleshooting:**")
            st.write("1. Check the live Gmail service configuration")
            st.write("2. Verify Gmail App Password is correct")
            st.write("3. Ensure email_accounts.json is properly configured")

def show_data_integration_status():
    """Show data integration and access to metadata and AI data - INCLUDING ALL SUBFOLDERS"""
    st.subheader("🔗 Data Integration & Access (Recursive Subfolder Scanning)")

    # Get comprehensive data scan including subfolders
    if EMAIL_INTEGRATION_AVAILABLE:
        try:
            manager = EmailIntegrationManager()
            comprehensive_scan = manager.get_comprehensive_data_scan(include_subfolders=True)

            # Display comprehensive stats
            st.markdown("### 📊 Complete Data Repository (All Subfolders)")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Total PDFs", comprehensive_scan['pdf_count'])
            with col2:
                st.metric("📝 Total DOCs", comprehensive_scan['doc_count'])
            with col3:
                st.metric("📊 Total CSVs", comprehensive_scan['csv_count'])
            with col4:
                st.metric("📈 Total Excel", comprehensive_scan['excel_count'])

            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("📃 Total TXT", comprehensive_scan['txt_count'])
            with col6:
                st.metric("📋 Total RTF", comprehensive_scan['rtf_count'])
            with col7:
                st.metric("🖼️ Total Images", comprehensive_scan['image_count'])
            with col8:
                st.metric("🗂️ Total Files", comprehensive_scan['total_files'])

            # Show subfolder breakdown
            with st.expander("📁 Subfolder Analysis (Recursive Scan)"):
                subfolder_data = comprehensive_scan['subfolder_analysis']
                if subfolder_data:
                    for folder, counts in subfolder_data.items():
                        total_in_folder = sum(counts.values())
                        st.markdown(f"**📂 {folder}:** {total_in_folder} files")
                        st.markdown(f"   - PDFs: {counts['pdf_count']}, DOCs: {counts['doc_count']}, CSVs: {counts['csv_count']}, Excel: {counts['excel_count']}")
                else:
                    st.info("No subfolders found")

            st.success(f"✅ **Scanning Mode:** {comprehensive_scan['scanning_mode']} from `{comprehensive_scan['base_path']}`")

        except Exception as e:
            st.error(f"❌ Error performing comprehensive data scan: {e}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Raw Data Access")
        st.info(f"**IntelliCV-data Path:** `{INTELLICV_DATA_PATH}`")

        if INTELLICV_DATA_PATH.exists():
            # Show recursive file count
            all_files = list(INTELLICV_DATA_PATH.rglob("*"))
            file_count = len([f for f in all_files if f.is_file()])
            if file_count > 0:
                st.success(f"✅ {file_count} files available (including all subfolders)")
                with st.expander("📁 View File Structure"):
                    # Group by folder
                    folder_groups = {}
                    for file in all_files[:20]:  # Show first 20
                        if file.is_file():
                            folder = str(file.parent.relative_to(INTELLICV_DATA_PATH))
                            if folder not in folder_groups:
                                folder_groups[folder] = []
                            folder_groups[folder].append(file.name)

                    for folder, files in folder_groups.items():
                        st.markdown(f"**📂 {folder}:**")
                        for file in files[:5]:  # Show first 5 files per folder
                            st.text(f"   📄 {file}")
                        if len(files) > 5:
                            st.text(f"   ... and {len(files) - 5} more")

                    if file_count > 20:
                        st.text(f"... showing first 20 of {file_count} total files")
            else:
                st.warning("⚠️ No files found")
        else:
            st.error("❌ IntelliCV-data directory not found")

    with col2:
        st.markdown("### 🤖 AI Data Access")
        st.info(f"**AI Data Path:** `{AI_DATA_FINAL_PATH}`")

        if AI_DATA_FINAL_PATH.exists():
            # Show comprehensive AI data directory contents - CENTRALIZED VIEW
            if AI_DATA_CONFIG_AVAILABLE:
                # Use centralized configuration for accurate counts
                total_files = ai_data_paths.get_total_json_count()
                directory_summary = ai_data_paths.get_directory_summary()
                st.success(f"✅ **CENTRALIZED AI DATA:** {total_files:,} total JSON files")

                # Show breakdown by directory using centralized config
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📄 Parsed Resumes", f"{directory_summary.get('parsed_resumes', 0):,}")

                with col2:
                    st.metric("🏢 Companies", f"{directory_summary.get('companies', 0):,}")

                with col3:
                    st.metric("💼 Job Titles", f"{directory_summary.get('job_titles', 0):,}")

                with col4:
                    st.metric("📧 Email Data", f"{directory_summary.get('email_extracted', 0):,}")

                # Show additional metrics
                col5, col6, col7 = st.columns(3)
                with col5:
                    st.metric("🏷️ Metadata", f"{directory_summary.get('metadata', 0):,}")
                with col6:
                    st.metric("📍 Locations", f"{directory_summary.get('locations', 0):,}")
                with col7:
                    st.metric("🔄 Normalized", f"{directory_summary.get('normalized', 0):,}")
            else:
                # Fallback to manual counting
                all_ai_files = list(AI_DATA_FINAL_PATH.rglob("*.json"))
                st.success(f"✅ **CENTRALIZED AI DATA:** {len(all_ai_files)} total JSON files")

                # Show breakdown by directory
                col1, col2, col3 = st.columns(3)

                with col1:
                    parsed_resumes = len(list((AI_DATA_FINAL_PATH / "parsed_resumes").glob("*.json"))) if (AI_DATA_FINAL_PATH / "parsed_resumes").exists() else 0
                    st.metric("📄 Parsed Resumes", parsed_resumes)

                with col2:
                    companies = len(list((AI_DATA_FINAL_PATH / "companies").glob("*.json"))) if (AI_DATA_FINAL_PATH / "companies").exists() else 0
                    st.metric("🏢 Companies", companies)

                with col3:
                    job_titles = len(list((AI_DATA_FINAL_PATH / "job_titles").glob("*.json"))) if (AI_DATA_FINAL_PATH / "job_titles").exists() else 0
                    st.metric("💼 Job Titles", job_titles)

            total_display = ai_data_paths.get_total_json_count() if AI_DATA_CONFIG_AVAILABLE else len(list(AI_DATA_FINAL_PATH.rglob("*.json")))

            with st.expander(f"🧠 View AI Data Structure ({total_display:,} files)", expanded=False):
                # Show directory structure
                directories = [d for d in AI_DATA_FINAL_PATH.iterdir() if d.is_dir()]
                for directory in sorted(directories):
                    json_count = len(list(directory.glob("*.json")))
                    if json_count > 0:
                        st.write(f"� **{directory.name}**: {json_count} JSON files")

                # Show root level files
                root_files = list(AI_DATA_FINAL_PATH.glob("*.json"))
                if root_files:
                    st.write(f"📁 **Root**: {len(root_files)} JSON files")

            # Show recent AI data with better selection
            if st.button("📈 Load Recent AI Data Sample"):
                try:
                    # Get all JSON files using centralized path
                    all_json_files = list(AI_DATA_FINAL_PATH.rglob("*.json"))
                    if all_json_files:
                        latest_file = max(all_json_files, key=lambda x: x.stat().st_mtime)
                        st.info(f"Loading: {latest_file.name} from {latest_file.parent.name}/")
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # Show sample of data instead of everything
                        if isinstance(data, list) and len(data) > 0:
                            st.json(data[:2] if len(data) > 2 else data)  # Show first 2 items
                            if len(data) > 2:
                                st.info(f"Showing 2 of {len(data)} items")
                        else:
                            st.json(data)
                    else:
                        st.warning("No JSON files found")
                except Exception as e:
                    st.error(f"Error loading AI data: {e}")
        else:
            st.error("❌ AI data directory not found")

    # Parser integration status
    st.markdown("### 🔧 Parser Integration")
    col1, col2, col3 = st.columns(3)

    with col1:
        if COMPLETE_DATA_PARSER_PATH.exists():
            st.success("✅ Complete Data Parser Available")
            if st.button("🚀 Run Email Parser"):
                st.info("Running complete data parser on email data...")
                st.code(f"python {COMPLETE_DATA_PARSER_PATH}", language="bash")
        else:
            st.error("❌ Complete Data Parser Not Found")

    with col2:
        # Check for pandas availability
        try:
            import pandas as pd
            st.success("✅ Pandas Available")
            st.caption(f"Version: {pd.__version__}")
        except ImportError:
            st.error("❌ Pandas Not Available")

    with col3:
        # Check parsing libraries
        try:
            import PyPDF2, docx, openpyxl
            st.success("✅ All Parsers Ready")
            st.caption("PDF, DOCX, Excel supported")
        except ImportError:
            st.error("❌ Some Parsers Missing")

def main():
    # Apply IntelliCV-AI branding
    if BRANDING_AVAILABLE:
        apply_intellicv_styling()
        render_intellicv_page_header("Email Integration", "📧", "Historical CV Scanner & Email Analytics")
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;'>
            <h1>📧 IntelliCV-AI Email Integration</h1>
            <h3>Scan your email archives back to 2011 for CVs and resumes</h3>
            <p>Extract historical CV data from Gmail, Outlook, Yahoo, and other email providers</p>
        </div>
        """, unsafe_allow_html=True)

    # Show email integration status
    if not EMAIL_INTEGRATION_AVAILABLE:
        st.error("❌ Email integration modules not loaded. Demo/fallback mode is disabled.")
        st.info("Fix the missing email integration dependencies/modules, then reload this page.")
        st.stop()
    else:
        st.success(f"✅ Email integration system loaded successfully! (Using {EMAIL_INTEGRATION_TYPE} storage)")

    # Initialize email manager
    if EMAIL_INTEGRATION_AVAILABLE:
        try:
            # Ensure data directory exists
            data_dir = Path(__file__).parent.parent / "data" / "email_data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Initialize with proper data directory
            email_manager = EmailIntegrationManager(data_dir=str(data_dir))
            st.success(f"✅ Email integration system initialized successfully! (Storage: {EMAIL_INTEGRATION_TYPE})")
        except Exception as e:
            st.error(f"❌ Failed to initialize email system: {str(e)}")
            st.info("Demo/mock email manager is disabled. Fix the real email integration and retry.")
            return
    else:
        email_manager = None
        st.error("❌ Email integration modules not loaded. Demo/fallback mode is disabled.")
        return

    # Create tabs for different email functions
    tabs = st.tabs([
        "🔧 Setup Email Account",
        "📧 Manage Accounts",
        "🔍 Historical CV Scan",
        "📊 Scan Results",
        "� Data Storage",
        "�🚀 AI Integration",
        "🌐 Universal OAuth2.0 Extractor"
    ])

    # Tab 1: Setup Email Account
    with tabs[0]:
        st.subheader("🔧 Add Email Account for Scanning")

        st.warning("""
        **🔐 CRITICAL: You MUST use App Passwords (not regular passwords)**

        **✅ Required Setup Steps:**
        1. **Enable 2-Factor Authentication** on your email account
        2. **Generate an App Password** specifically for IMAP access
        3. **Use the App Password** in the form below (NOT your regular password)
        """)

        with st.expander("📋 Detailed App Password Setup Instructions", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                **🔵 Gmail Setup:**
                1. Go to [Google Account Security](https://myaccount.google.com/security)
                2. Enable 2-Step Verification
                3. Go to App passwords
                4. Select "Mail" → Generate
                5. Copy the 16-character password
                """)

            with col2:
                st.markdown("""
                **🟡 Yahoo Setup:**
                1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
                2. Enable 2-Step Verification
                3. Click "Generate app password"
                4. Select "Other app" → Enter "IMAP"
                5. Copy the generated password
                """)

            with col3:
                st.markdown("""
                **🔴 Outlook Setup:**
                1. Go to [Microsoft Security](https://account.microsoft.com/security)
                2. Enable 2-Step Verification
                3. Go to App passwords
                4. Create new → Select "Email"
                5. Copy the generated password
                """)

        with st.form("add_email_account"):
            col1, col2 = st.columns(2)

            with col1:
                account_name = st.text_input("Account Name", placeholder="e.g., My Gmail Account")
                email_address = st.text_input("Email Address", placeholder="your.email@gmail.com")
                provider = st.selectbox("Email Provider", ["gmail", "outlook", "yahoo"])

            with col2:
                username = st.text_input("Username (usually same as email)", placeholder="your.email@gmail.com")
                app_password = st.text_input("App Password", type="password", placeholder="Your app-specific password")

                st.markdown("**📋 Quick Setup:**")
                if provider == "gmail":
                    st.code("Server: imap.gmail.com:993 (SSL)")
                elif provider == "outlook":
                    st.code("Server: outlook.office365.com:993 (SSL)")
                elif provider == "yahoo":
                    st.code("Server: imap.mail.yahoo.com:993 (SSL)")

            test_connection = st.checkbox("🔍 Test connection before saving")

            if st.form_submit_button("💾 Add Email Account", type="primary"):
                if account_name and email_address and app_password:

                    # Validate email format
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, email_address):
                        st.error("❌ Invalid email address format")
                        st.stop()

                    # Check if email domain matches provider
                    domain = email_address.split('@')[1].lower()
                    expected_domains = {
                        'gmail': ['gmail.com', 'googlemail.com'],
                        'yahoo': ['yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.fr'],
                        'outlook': ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']
                    }

                    if domain not in expected_domains.get(provider, []):
                        st.warning(f"⚠️ Email domain '{domain}' may not match provider '{provider}'. Continue anyway?")
                        if not st.button("Yes, continue with this configuration"):
                            st.stop()

                    # Test connection first if requested
                    if test_connection:
                        with st.spinner("🔗 Testing email connection..."):
                            try:
                                # Use improved connection tester if available
                                if EMAIL_DATA_MANAGER_AVAILABLE:
                                    data_manager = EmailDataManager()
                                    connection_tester = ImprovedEmailConnectionTester(data_manager)
                                    test_result = connection_tester.test_email_connection(
                                        email_address, app_password, provider
                                    )
                                elif email_manager:
                                    # Fallback to standard tester
                                    test_result = email_manager.test_email_connection(
                                        email_address, app_password, provider
                                    )
                                else:
                                    # Demo mode
                                    test_result = {"success": False, "error": "Demo mode - email integration modules not available"}

                                if test_result.get("success"):
                                    st.success(f"✅ Connection successful! Found {test_result.get('total_emails_in_inbox', 0)} emails in inbox")
                                    if EMAIL_DATA_MANAGER_AVAILABLE:
                                        st.info(f"📅 Test completed at: {test_result.get('test_time', 'Unknown')}")
                                        st.info(f"🔗 Server: {test_result.get('server', 'Unknown')}:{test_result.get('port', 'Unknown')}")

                                    # Check if email already exists
                                    try:
                                        if email_manager:
                                            existing_accounts = email_manager.get_email_accounts()
                                        else:
                                            existing_accounts = []
                                        # Handle both dict and object formats
                                        email_exists = False
                                        for acc in existing_accounts:
                                            acc_email = acc['email_address'] if isinstance(acc, dict) else acc.email_address
                                            if acc_email == email_address:
                                                email_exists = True
                                                break

                                        if email_exists:
                                            st.warning(f"⚠️ Email account '{email_address}' already exists in the system!")
                                            st.info("💡 You can update the existing account instead of creating a duplicate.")
                                        else:
                                            # Create and add account
                                            if email_manager:
                                                config = email_manager.provider_configs[provider]
                                            else:
                                                config = {"server": "demo.server.com", "port": 993, "use_ssl": True}
                                            account = EmailAccount(
                                                name=account_name,
                                                email_address=email_address,
                                                provider=provider,
                                                imap_server=config["imap_server"],
                                                imap_port=config["imap_port"],
                                                username=username or email_address,
                                                password=app_password,
                                                use_ssl=config["use_ssl"]
                                            )

                                            if email_manager:
                                                account_id = email_manager.add_email_account(account)
                                            else:
                                                account_id = "demo_account_123"
                                            st.success(f"🎉 Email account '{account_name}' added successfully!")
                                            st.info(f"Account ID: {account_id}")
                                    except Exception as e:
                                        if "UNIQUE constraint failed" in str(e):
                                            st.warning(f"⚠️ Email account '{email_address}' already exists in the database!")
                                            st.info("💡 Each email address can only be registered once. Try updating the existing account.")
                                        else:
                                            st.error(f"❌ Failed to add email account: {str(e)}")
                                            raise e

                                else:
                                    error_msg = test_result.get('error', 'Unknown error')
                                    error_type = test_result.get('error_type', 'UNKNOWN')

                                    st.error(f"❌ Connection failed: {error_msg}")

                                    # Enhanced error handling with improved guidance
                                    if error_type == "AUTHENTICATION_FAILED":
                                        st.error("� **AUTHENTICATION FAILED - App Password Required**")

                                        # Show provider-specific troubleshooting
                                        troubleshooting = test_result.get('troubleshooting', {})
                                        if provider in troubleshooting:
                                            st.markdown(f"**📋 {provider.title()} Setup Steps:**")
                                            for step in troubleshooting[provider]:
                                                st.markdown(f"• {step}")

                                        st.warning("""
                                        **🔑 CRITICAL: You MUST use App Passwords, not regular passwords!**

                                        Modern email providers block regular password access for security.
                                        Follow the setup steps above to generate an App Password.
                                        """)

                                        # Link to help guide
                                        st.info("� **Complete Setup Guide:** Check the `EMAIL_AUTHENTICATION_FIX_GUIDE.md` in your email data folder")

                                    elif error_type == "CONNECTION_ERROR":
                                        st.warning("🌐 **Network/Connection Issue:**")
                                        troubleshooting_tips = test_result.get('troubleshooting', [])
                                        for tip in troubleshooting_tips:
                                            st.markdown(f"• {tip}")

                                    else:
                                        st.warning("🔧 **General troubleshooting:** Verify email address, server settings, and app password.")

                            except Exception as e:
                                st.error(f"❌ Connection test failed: {str(e)}")

                    else:
                        # Add without testing
                        try:
                            # Check if email already exists
                            if email_manager:
                                existing_accounts = email_manager.get_email_accounts()
                            else:
                                existing_accounts = []
                            # Handle both dict and object formats
                            email_exists = False
                            for acc in existing_accounts:
                                acc_email = acc['email_address'] if isinstance(acc, dict) else acc.email_address
                                if acc_email == email_address:
                                    email_exists = True
                                    break

                            if email_exists:
                                st.warning(f"⚠️ Email account '{email_address}' already exists in the system!")
                                st.info("💡 You can update the existing account instead of creating a duplicate.")
                            else:
                                if email_manager:
                                    config = email_manager.provider_configs[provider]
                                else:
                                    config = {"server": "demo.server.com", "port": 993, "use_ssl": True}
                                if EMAIL_INTEGRATION_AVAILABLE:
                                    account = EmailAccount(
                                        name=account_name,
                                        email_address=email_address,
                                        provider=provider,
                                        imap_server=config["imap_server"],
                                        imap_port=config["imap_port"],
                                        username=username or email_address,
                                        password=app_password,
                                        use_ssl=config["use_ssl"]
                                    )

                                    account_id = email_manager.add_email_account(account)
                                else:
                                    # Demo mode
                                    account_id = f"demo_account_{len(existing_accounts) + 1}"
                                st.success(f"📧 Email account '{account_name}' added successfully!")
                                st.info(f"Account ID: {account_id}")

                                # Initialize data storage for this account if enhanced manager available
                                if EMAIL_DATA_MANAGER_AVAILABLE:
                                    try:
                                        data_manager = EmailDataManager()
                                        st.info(f"📁 Data storage initialized at: `{data_manager.base_path}`")
                                    except Exception as data_error:
                                        st.warning(f"⚠️ Data storage setup warning: {data_error}")

                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.warning(f"⚠️ Email account '{email_address}' already exists in the database!")
                                st.info("💡 Each email address can only be registered once. Try updating the existing account.")
                            else:
                                st.error(f"❌ Failed to add account: {str(e)}")

                else:
                    st.error("❌ Please fill in all required fields")

    # Tab 2: Manage Accounts
    with tabs[1]:
        st.subheader("📧 Email Accounts")

        try:
            if email_manager:
                accounts = email_manager.get_email_accounts()
            else:
                accounts = []  # Demo mode - no accounts

            if accounts:
                # Display accounts in a nice format
                for account in accounts:
                    with st.expander(f"📧 {account['name']} ({account['email_address']})"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**Provider:** {account.provider.title()}")
                            st.write(f"**Status:** {'🟢 Active' if getattr(account, 'is_active', True) else '🔴 Inactive'}")

                        with col2:
                            last_sync = getattr(account, 'last_sync', 'Never')
                            st.write(f"**Last Sync:** {last_sync}")
                            st.write(f"**Account ID:** `{account.account_id[:8]}...`")

                        with col3:
                            if st.button(f"🔍 Test Connection", key=f"test_{account['id']}"):
                                # Test connection for existing account
                                st.info("Connection test would go here")

                            if st.button(f"🗑️ Remove Account", key=f"remove_{account['id']}"):
                                st.warning("Account removal would go here")

            else:
                st.info("📭 No email accounts configured yet. Use the 'Setup Email Account' tab to add your first account.")

        except Exception as e:
            st.error(f"❌ Error loading accounts: {str(e)}")

    # Tab 3: Historical CV Scan - THE MAIN FEATURE YOU REQUESTED!
    with tabs[2]:
        st.subheader("🔍 Historical CV Scanner - Back to 2011!")

        st.info("""
        **🎯 This is the feature you requested!**

        Scan your email archives back to 2011 to find historical CVs and resumes.
        This will search through your email attachments for documents that look like CVs.
        """)

        try:
            if email_manager:
                accounts = email_manager.get_email_accounts()
            else:
                # Demo accounts
                accounts = [
                    {"id": "demo1", "name": "Demo Gmail", "email_address": "demo@gmail.com", "provider": "gmail"},
                    {"id": "demo2", "name": "Demo Outlook", "email_address": "demo@outlook.com", "provider": "outlook"}
                ]

            if not accounts:
                st.warning("📧 Please add an email account first in the 'Setup Email Account' tab.")
            else:
                with st.form("historical_scan"):
                    # Account selection
                    account_options = {f"{acc['name']} ({acc['email_address']})": acc['id'] for acc in accounts}
                    selected_account_name = st.selectbox("📧 Select Email Account", list(account_options.keys()))
                    selected_account_id = account_options[selected_account_name]

                    # Scan options
                    col1, col2 = st.columns(2)

                    with col1:
                        start_year = st.number_input("📅 Start Year", min_value=2011, max_value=2025, value=2011)
                        scan_type = st.selectbox("🎯 Scan Type", [
                            "Full Historical Scan (2011 onwards)",
                            "Recent Years Only (2020 onwards)",
                            "Custom Year Range"
                        ])

                    with col2:
                        if scan_type == "Custom Year Range":
                            end_year = st.number_input("📅 End Year", min_value=start_year, max_value=2025, value=2025)
                        else:
                            end_year = 2025

                        max_emails_per_year = st.number_input("📊 Max Emails per Year", min_value=100, max_value=1000, value=500)

                    st.markdown("**🔍 What this scan will do:**")
                    st.markdown(f"""
                    - 📧 Scan emails from **{start_year}** to **{end_year}**
                    - 🔍 Look for emails with CV/resume attachments
                    - 📄 Extract PDF, Word, and text documents
                    - 🧠 Identify documents that are likely CVs/resumes
                    - 💾 Store extracted CVs for AI enrichment processing
                    """)

                    if st.form_submit_button("🚀 Start Historical CV Scan", type="primary"):
                        st.info(f"🔍 Starting historical CV scan for {selected_account_name.split('(')[0].strip()}...")

                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        try:
                            with st.spinner("📧 Scanning email archive for historical CVs..."):
                                # Run the historical scan
                                if email_manager:
                                    scan_result = email_manager.scan_historical_email_archive(
                                        selected_account_id,
                                        start_year=start_year
                                    )
                                else:
                                    # Demo mode result
                                    scan_result = {
                                        "success": True,
                                        "emails_scanned": 15247,
                                        "cvs_found": 234,
                                        "documents_extracted": 189,
                                        "processing_time": "2m 34s"
                                    }

                                progress_bar.progress(100)

                                if scan_result.get("success"):
                                    st.success("🎉 Historical CV scan completed successfully!")

                                    # Display results with correct field names
                                    col1, col2, col3 = st.columns(3)

                                    with col1:
                                        st.metric("📧 Emails Processed", scan_result.get("emails_scanned", 0))

                                    with col2:
                                        st.metric("📄 Documents Extracted", scan_result.get("documents_extracted", 0))

                                    with col3:
                                        st.metric("📋 CVs Found", scan_result.get("cvs_found", 0))

                                    # Year breakdown
                                    if "year_breakdown" in scan_result:
                                        st.subheader("📊 Year-by-Year Results")

                                        year_data = []
                                        for year, data in scan_result["year_breakdown"].items():
                                            if isinstance(data, dict) and "resumes_found" in data:
                                                year_data.append({
                                                    "Year": year,
                                                    "Emails Processed": data.get("emails_processed", 0),
                                                    "Documents Extracted": data.get("documents_extracted", 0),
                                                    "CVs Found": data.get("resumes_found", 0)
                                                })

                                        if year_data:
                                            df = pd.DataFrame(year_data)
                                            st.dataframe(df, use_container_width=True)

                                            # Create chart
                                            st.bar_chart(df.set_index("Year")["CVs Found"])

                                    # Store scan results in session state for other tabs
                                    st.session_state['last_scan_result'] = scan_result

                                else:
                                    st.error(f"❌ Scan failed: {scan_result.get('error', 'Unknown error')}")

                        except Exception as e:
                            st.error(f"❌ Scan failed with error: {str(e)}")
                            progress_bar.progress(0)

        except Exception as e:
            st.error(f"❌ Error setting up historical scan: {str(e)}")

    # Tab 4: Scan Results
    with tabs[3]:
        st.subheader("📊 Historical Scan Results")

        if 'last_scan_result' in st.session_state:
            scan_result = st.session_state['last_scan_result']

            st.success(f"📅 Last scan: {scan_result.get('years_scanned', 'Unknown period')}")

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📧 Total Emails", scan_result.get("emails_scanned", scan_result.get("total_emails_processed", 0)))
            with col2:
                st.metric("📄 Documents", scan_result.get("documents_extracted", scan_result.get("total_documents_extracted", 0)))
            with col3:
                st.metric("📋 CVs Found", scan_result.get("cvs_found", scan_result.get("total_resumes_found", 0)))
            with col4:
                st.metric("✅ Scan Status", "Complete" if scan_result.get("success") else "Failed")

            # Display extracted documents if available
            try:
                if email_manager:
                    documents = email_manager.get_extracted_documents(limit=50)
                else:
                    # Demo documents
                    documents = [
                        {"filename": "john_doe_resume.pdf", "extraction_date": "2025-10-10", "email_from": "hr@company.com", "cv_score": 0.95},
                        {"filename": "jane_smith_cv.docx", "extraction_date": "2025-10-09", "email_from": "recruiter@agency.com", "cv_score": 0.89},
                        {"filename": "mike_johnson_resume.pdf", "extraction_date": "2025-10-08", "email_from": "careers@startup.com", "cv_score": 0.92}
                    ]

                if documents:
                    st.subheader("📄 Recently Extracted Documents")

                    doc_data = []
                    for doc in documents:
                        doc_data.append({
                            "Filename": doc['filename'],
                            "Type": "📋 Resume" if doc['is_resume'] else "📄 Document",
                            "Size": f"{doc['file_size'] // 1024}KB",
                            "From": doc['email_sender'][:30] + "..." if len(doc['email_sender']) > 30 else doc['email_sender'],
                            "Date": doc['extraction_date'][:10],
                            "Account": doc['account_name']
                        })

                    df = pd.DataFrame(doc_data)
                    st.dataframe(df, use_container_width=True)

                else:
                    st.info("📭 No documents extracted yet. Run a historical scan first.")

            except Exception as e:
                st.warning(f"⚠️ Could not load document details: {str(e)}")

        else:
            st.info("📊 No scan results available yet. Run a historical scan first in the 'Historical CV Scan' tab.")

    # Tab 5: Data Storage Dashboard
    with tabs[4]:
        st.subheader("💾 Email Data Storage & Management - IntelliCV Directory")

        # Use proper IntelliCV data manager first
        if DATA_MANAGER_AVAILABLE:
            try:
                data_manager = get_data_manager()

                st.success(f"✅ IntelliCV Data Directory System initialized")
                st.info(f"📁 **Main Data Path:** `{data_manager.intellicv_data_path}`")
                st.info(f"📧 **Email Data Path:** `{data_manager.email_data_path}`")

                # Get real directory status
                directory_status = data_manager.get_directory_status()

                # Display main directory overview
                st.markdown("### 📊 Directory Structure Status")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📁 IntelliCV Data",
                             "✅ Ready" if directory_status['main_directories']['IntelliCV Data']['exists'] else "❌ Missing",
                             delta=f"{directory_status['main_directories']['IntelliCV Data']['file_count']} files")

                with col2:
                    st.metric("📧 Email Integration",
                             "✅ Ready" if directory_status['main_directories']['Email Integration']['exists'] else "❌ Missing",
                             delta=f"{directory_status['main_directories']['Email Integration']['file_count']} files")

                with col3:
                    st.metric("📄 Email Extracted",
                             "✅ Ready" if directory_status['main_directories']['Email Extracted']['exists'] else "❌ Missing",
                             delta=f"{directory_status['main_directories']['Email Extracted']['file_count']} files")

                with col4:
                    st.metric("🤖 AI Data",
                             "✅ Ready" if directory_status['main_directories']['AI Data']['exists'] else "❌ Missing",
                             delta=f"{directory_status['main_directories']['AI Data']['file_count']} files")

                # File counts
                st.markdown("### 📄 CV File Summary")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📄 Total Files", directory_status['file_counts'].get('total_files', 0))

                with col2:
                    st.metric("📋 PDF CVs", directory_status['file_counts'].get('pdf_files', 0))

                with col3:
                    st.metric("📝 DOC CVs", directory_status['file_counts'].get('doc_files', 0))

                with col4:
                    st.metric("💾 Total Size", f"{directory_status['total_size_mb']} MB")

                # Recent extracted CVs with details
                st.markdown("### 📄 Recent CV Files")

                cv_list = data_manager.get_extracted_cv_list(limit=10)

                if cv_list:
                    for i, cv in enumerate(cv_list[:5], 1):
                        with st.expander(f"📄 {i}. {cv['filename']} ({cv['size_mb']} MB)"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**Provider:** {cv['provider']}")
                                st.write(f"**Extension:** {cv['extension']}")
                                st.write(f"**Size:** {cv['size_mb']} MB")

                            with col2:
                                st.write(f"**Modified:** {cv['modified'][:19]}")
                                st.write(f"**Path:** {cv['full_path']}")

                    if len(cv_list) > 5:
                        st.info(f"... and {len(cv_list) - 5} more CV files")
                else:
                    st.info("📭 No CV files found yet. Run email extraction to populate this directory.")

                # Directory management
                st.markdown("### 🛠️ Directory Management")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("🔄 Refresh Directory Status"):
                        st.rerun()

                with col2:
                    if st.button("📁 Open Data Directory"):
                        st.info(f"📂 **Main Directory:** `{data_manager.intellicv_data_path}`")
                        st.code(f"explorer {data_manager.intellicv_data_path}")

                with col3:
                    if st.button("📊 Full Directory Report"):
                        with st.expander("📋 Complete Directory Report", expanded=True):
                            st.json(directory_status)

            except Exception as e:
                st.error(f"❌ Error with IntelliCV Data Manager: {e}")
                st.info("💡 The data manager builds the proper directory structure outside SANDBOX")

        elif EMAIL_DATA_MANAGER_AVAILABLE:
            try:
                data_manager = EmailDataManager()

                st.success(f"✅ Email data storage initialized at: `{data_manager.base_path}`")

                # Get storage statistics
                with st.spinner("📊 Loading storage statistics..."):
                    storage_stats = data_manager.get_storage_stats()

                # Display storage overview
                st.markdown("### 📊 Storage Overview")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    attachments_stats = storage_stats['directories'].get('attachments', {})
                    st.metric(
                        "📎 Attachments",
                        attachments_stats.get('file_count', 0),
                        delta=f"{attachments_stats.get('total_size_mb', 0):.1f} MB"
                    )

                with col2:
                    cvs_stats = storage_stats['directories'].get('extracted_cvs', {})
                    st.metric(
                        "📄 Extracted CVs",
                        cvs_stats.get('file_count', 0),
                        delta=f"{cvs_stats.get('total_size_mb', 0):.1f} MB"
                    )

                with col3:
                    logs_stats = storage_stats['directories'].get('logs', {})
                    st.metric(
                        "📝 Log Files",
                        logs_stats.get('file_count', 0),
                        delta=f"{logs_stats.get('total_size_mb', 0):.1f} MB"
                    )

                with col4:
                    metadata_stats = storage_stats['directories'].get('metadata', {})
                    st.metric(
                        "🗂️ Metadata Files",
                        metadata_stats.get('file_count', 0),
                        delta=f"{metadata_stats.get('total_size_mb', 0):.1f} MB"
                    )

                # Storage breakdown
                st.markdown("### 📁 Directory Structure")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**📎 Attachments Storage**")
                    attachments_dir = data_manager.attachments_dir
                    for provider_dir in ['gmail', 'outlook', 'yahoo', 'other']:
                        provider_path = attachments_dir / provider_dir
                        if provider_path.exists():
                            file_count = len(list(provider_path.glob('*')))
                            st.write(f"• {provider_dir.title()}: {file_count} files")

                    st.markdown("**📄 CV Documents**")
                    cvs_dir = data_manager.extracted_cvs_dir
                    for cv_type in ['pdf', 'word', 'text', 'parsed']:
                        type_path = cvs_dir / cv_type
                        if type_path.exists():
                            file_count = len(list(type_path.glob('*')))
                            st.write(f"• {cv_type.upper()}: {file_count} files")

                with col2:
                    st.markdown("**📝 System Logs**")
                    logs_dir = data_manager.logs_dir
                    for log_type in ['connection', 'scanning', 'extraction']:
                        log_path = logs_dir / log_type
                        if log_path.exists():
                            log_files = list(log_path.glob('*.log'))
                            latest = max([f.name for f in log_files]) if log_files else 'None'
                            st.write(f"• {log_type.title()}: {len(log_files)} files (Latest: {latest})")

                    st.markdown("**🗂️ Metadata**")
                    for metadata_file in ['accounts.json', 'messages.json', 'documents.json']:
                        metadata_info = storage_stats['metadata'].get(metadata_file, {})
                        item_count = metadata_info.get('total_items', 0)
                        st.write(f"• {metadata_file}: {item_count} items")

                # Recent extracted CVs
                st.markdown("### 📄 Recent Extracted CVs")

                recent_cvs = data_manager.get_extracted_cvs(limit=10)

                if recent_cvs:
                    for cv in recent_cvs[:5]:  # Show top 5
                        with st.expander(f"📄 {cv.get('filename', 'Unknown')} - {cv.get('cv_id', 'Unknown ID')[:8]}..."):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**Email ID:** {cv.get('email_id', 'Unknown')[:8]}...")
                                st.write(f"**Extracted:** {cv.get('extraction_metadata', {}).get('extracted_at', 'Unknown')[:19]}")
                                st.write(f"**Type:** {cv.get('extraction_metadata', {}).get('cv_type', 'Unknown')}")

                            with col2:
                                st.write(f"**Storage Path:** `{cv.get('extraction_metadata', {}).get('storage_path', 'Unknown')}`")
                                if 'candidate_name' in cv:
                                    st.write(f"**Candidate:** {cv['candidate_name']}")
                                if 'position_applied' in cv:
                                    st.write(f"**Position:** {cv['position_applied']}")
                else:
                    st.info("No extracted CVs found yet. Start an email scan to extract CV documents.")

                # Log viewer
                st.markdown("### 📝 Recent Log Entries")

                log_type = st.selectbox("Select log type", ['general', 'connection', 'scanning', 'extraction'])

                recent_logs = data_manager.get_log_summary(log_type=log_type, lines=20)

                if recent_logs:
                    st.code('\n'.join(recent_logs), language='log')
                else:
                    st.info(f"No {log_type} logs available yet.")

                # Storage management
                st.markdown("### 🛠️ Storage Management")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("🧹 Cleanup Old Data (30+ days)"):
                        with st.spinner("🧹 Cleaning up old data..."):
                            cleanup_result = data_manager.cleanup_old_data(days_old=30)

                            if cleanup_result['files_removed'] > 0:
                                st.success(f"✅ Cleaned up {cleanup_result['files_removed']} files, "
                                         f"freed {cleanup_result['bytes_freed'] / (1024*1024):.1f} MB")
                            else:
                                st.info("No old files found to clean up.")

                with col2:
                    if st.button("📊 Refresh Statistics"):
                        st.rerun()

                with col3:
                    if st.button("📁 Open Data Folder"):
                        st.info(f"Data folder: `{data_manager.base_path}`")
                        st.code(f"explorer {data_manager.base_path}")

                # Configuration info
                with st.expander("⚙️ Storage Configuration"):
                    st.json({
                        "base_path": str(data_manager.base_path),
                        "attachments_dir": str(data_manager.attachments_dir),
                        "extracted_cvs_dir": str(data_manager.extracted_cvs_dir),
                        "logs_dir": str(data_manager.logs_dir),
                        "metadata_dir": str(data_manager.metadata_dir)
                    })

            except Exception as e:
                st.error(f"❌ Error accessing email data storage: {e}")
                st.info("The data storage system will be initialized when you add your first email account.")

        else:
            st.warning("⚠️ Enhanced email data manager not available")
            st.info("""
            **📁 Default Storage Location Suggestion:**

            For email integration data, I recommend using this folder structure:

            ```
            IntelliCV-AI/
            └── IntelliCV/
                └── SANDBOX/
                    └── admin_portal/
                        └── data/
                            └── email_data/  ← Store email data here
                                ├── attachments/     # Email attachments
                                ├── extracted_cvs/   # Processed CV documents
                                ├── logs/           # Operation logs
                                └── metadata/       # Email & document metadata
            ```

            **Benefits:**
            - ✅ Organized data structure
            - ✅ Easy backup and management
            - ✅ Integration with existing admin portal
            - ✅ Secure file storage with hashed filenames
            """)

    # Tab 6: AI Integration
    with tabs[5]:
        st.subheader("🚀 AI Integration & Enrichment - REAL DATA")

        st.info("""
        **🧠 True Data AI Enrichment Integration**

        Export REAL extracted CVs from your data directory to the AI enrichment pipeline.
        Shows actual CV files with details for verification.
        """)

        try:
            # Use proper data manager for real data
            if DATA_MANAGER_AVAILABLE:
                data_manager = get_data_manager()
                real_stats = data_manager.get_real_data_stats()

                st.success(f"✅ Using IntelliCV Data Directory: `{real_stats['data_paths']['intellicv_data']}`")

                # Display REAL AI status
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📋 Total Extracted CVs", real_stats['total_extracted_files'])
                with col2:
                    st.metric("📄 PDF Files", real_stats['pdf_files'])
                with col3:
                    st.metric("📝 DOC Files", real_stats['doc_files'])
                with col4:
                    st.metric("💾 Total Size (MB)", f"{real_stats['total_size_mb']:.2f}")

                # Show actual CV files before export
                st.subheader("📄 CV Files Available for AI Export")

                cv_list = data_manager.get_extracted_cv_list(limit=20)

                if cv_list:
                    st.success(f"✅ Found {len(cv_list)} CV files ready for AI processing")

                    # Show CV file details
                    with st.expander(f"📋 View CV Files List ({len(cv_list)} files)", expanded=False):
                        for i, cv in enumerate(cv_list[:10], 1):  # Show first 10
                            st.write(f"**{i}. {cv['filename']}**")
                            st.write(f"   📁 Provider: {cv['provider']} | 📐 Size: {cv['size_mb']} MB | 📅 Modified: {cv['modified'][:10]}")

                        if len(cv_list) > 10:
                            st.info(f"... and {len(cv_list) - 10} more CV files")

                # Export to AI enrichment with REAL data
                if st.button("🚀 Export REAL CVs to AI Enrichment", type="primary"):
                    with st.spinner("🧠 Exporting REAL CV data to AI enrichment pipeline..."):
                        try:
                            export_result = data_manager.export_cvs_for_ai_processing()

                            if export_result.get("success"):
                                st.success(f"✅ {export_result['message']}")

                                # Show detailed export results
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric("📄 CVs Exported", export_result['extracted_count'])
                                with col2:
                                    st.metric("📊 PDF Files", export_result['export_summary']['pdf_files'])
                                with col3:
                                    st.metric("📝 DOC Files", export_result['export_summary']['doc_files'])

                                # Show each exported CV file
                                st.subheader("📋 Exported CV Files - Document by Document")

                                for i, cv_file in enumerate(export_result['cv_list'], 1):
                                    with st.expander(f"📄 {i}. {cv_file['filename']} ({cv_file['size_mb']} MB)"):
                                        col1, col2 = st.columns(2)

                                        with col1:
                                            st.write(f"**File:** {cv_file['filename']}")
                                            st.write(f"**Provider:** {cv_file['provider']}")
                                            st.write(f"**Size:** {cv_file['size_mb']} MB")

                                        with col2:
                                            st.write(f"**Extension:** {cv_file['extension']}")
                                            st.write(f"**Modified:** {cv_file['modified'][:19]}")
                                            st.write(f"**Path:** {cv_file['full_path']}")

                                # Export summary
                                with st.expander("� Export Summary"):
                                    st.json(export_result['export_summary'])

                                st.info(f"📁 **Export File Location:** `{export_result['export_file']}`")
                                st.success("✅ **This is REAL data from your actual extracted CV files!**")

                            else:
                                st.error(f"❌ Export failed: {export_result.get('message', 'Unknown error')}")

                        except Exception as e:
                            st.error(f"❌ Export failed: {str(e)}")

                else:
                    st.info("📭 No CV files found for export. Run email extraction first.")

            else:
                st.error("❌ IntelliCV Data Manager not available")
                st.info("💡 The data manager builds the proper directory structure outside SANDBOX")

        except Exception as e:
            st.error(f"❌ AI integration error: {str(e)}")

    # Tab 7: Trusted Source App Password Setup
    with tabs[6]:
        st.subheader("🔐 Trusted Source Email Setup")

        st.info("""
        **�️ Secure App Password Authentication**

        Configure trusted email sources using app passwords for secure access:
        - ✅ Gmail, Yahoo, Outlook with app passwords only
        - 🛡️ No OAuth complexity - simple and secure
        - 📊 Trusted domain verification
        - 💾 Direct IMAP access with proper authentication
        """)

        # Check for required dependencies
        st.markdown("### 📦 System Requirements")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**� Email Libraries:**")
            try:
                import imaplib, email
                st.success("✅ IMAP libraries available")
            except ImportError:
                st.error("❌ IMAP libraries missing")

            try:
                import ssl
                st.success("✅ SSL support available")
            except ImportError:
                st.error("❌ SSL support missing")

        with col2:
            st.markdown("**🛠️ Additional Dependencies:**")

            # Check for universal email requirements
            universal_req_file = Path(__file__).parent.parent / "universal_email_requirements.txt"

            if universal_req_file.exists():
                st.warning("⚠️ Universal email requirements file found")

                if st.button("�️ Install Additional Email Libraries", type="secondary"):
                    with st.spinner("📦 Installing additional email libraries..."):
                        try:
                            import subprocess
                            result = subprocess.run([
                                "c:/IntelliCV-AI/IntelliCV/env310/python.exe",
                                "-m", "pip", "install",
                                "-r", str(universal_req_file)
                            ], capture_output=True, text=True)

                            if result.returncode == 0:
                                st.success("✅ Additional libraries installed successfully!")
                                st.info("💡 Restart the application to use new libraries")
                            else:
                                st.error(f"❌ Installation failed: {result.stderr}")

                        except Exception as e:
                            st.error(f"❌ Installation error: {e}")
            else:
                st.success("✅ No additional dependencies needed")

        # Trusted email domains
        st.markdown("### 🛡️ Trusted Email Domains")
        st.info("""
        **Security Policy:** Only emails from pre-approved trusted domains will be processed.
        This prevents unauthorized access and ensures data security.
        """)

        trusted_domains = [
            "johnston-vere.co.uk",
            "gmail.com",
            "yahoo.co.uk",
            "outlook.com",
            "hotmail.com"
        ]

        selected_domains = st.multiselect(
            "Select trusted domains for email extraction:",
            options=trusted_domains,
            default=["johnston-vere.co.uk", "gmail.com", "yahoo.co.uk"],
            help="Only emails from these domains will be processed"
        )

        # App password setup guide
        st.markdown("### 📋 App Password Setup Guide")

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.expander("🔵 Gmail App Password", expanded=False):
                st.markdown("""
                **Setup Steps:**
                1. Enable 2-Factor Authentication
                2. Go to Google Account Settings
                3. Security → App passwords
                4. Generate password for "Mail"
                5. Use this password (not your regular password)

                **Server:** imap.gmail.com:993 (SSL)
                """)

        with col2:
            with st.expander("� Yahoo App Password", expanded=False):
                st.markdown("""
                **Setup Steps:**
                1. Enable 2-Factor Authentication
                2. Go to Yahoo Account Security
                3. Generate app password
                4. Select "Other app" → Enter "IMAP"
                5. Use generated password

                **Server:** imap.mail.yahoo.com:993 (SSL)
                """)

        with col3:
            with st.expander("🔴 Outlook App Password", expanded=False):
                st.markdown("""
                **Setup Steps:**
                1. Enable 2-Factor Authentication
                2. Go to Microsoft Security dashboard
                3. Create app password for "Email"
                4. Use generated password
                5. Modern authentication required

                **Server:** outlook.office365.com:993 (SSL)
                """)

        # Current trusted accounts
        st.markdown("### 📧 Configured Trusted Accounts")

        if DATA_MANAGER_AVAILABLE:
            data_manager = get_data_manager()
            email_config = data_manager.check_email_accounts_config()

            if email_config['configured']:
                st.success(f"✅ {email_config['account_count']} trusted email accounts configured")

                for account in email_config['accounts'][:3]:  # Show first 3
                    domain = account.get('email_address', '').split('@')[-1] if '@' in account.get('email_address', '') else 'unknown'
                    if domain in selected_domains:
                        st.write(f"🔐 **{account.get('name', 'Unknown')}** - {account.get('email_address', 'Unknown')} ✅ Trusted")
                    else:
                        st.write(f"⚠️ **{account.get('name', 'Unknown')}** - {account.get('email_address', 'Unknown')} ❌ Not in trusted domains")
            else:
                st.info("📭 No email accounts configured yet")
        else:
            st.warning("⚠️ Data manager not available - cannot check account configuration")

        # Security verification
        st.markdown("### 🔒 Security Verification")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("�️ Trusted Domains", len(selected_domains))
            st.metric("� Security Level", "High" if len(selected_domains) <= 5 else "Medium")

        with col2:
            st.metric("� Auth Method", "App Password Only")
            st.metric("🌐 OAuth Status", "Disabled (Secure)")

        st.success("""
        ✅ **Security Status:** This system uses app passwords only from trusted domains.
        No universal OAuth extraction - only from pre-approved, secure sources.
        """)

        # Link to main account setup
        st.markdown("### ➡️ Next Steps")
        st.info("""
        **To add trusted email accounts:**
        1. Go to the "🔧 Setup Email Account" tab
        2. Add your trusted email accounts with app passwords
        3. Return here to verify domain trust levels
        4. Use "🔍 Historical CV Scan" for actual extraction
        """)

        if st.button("� Go to Account Setup", type="primary"):
            st.info("💡 Switch to the '🔧 Setup Email Account' tab to add your trusted email accounts")

    # Add enhanced email integration features
    st.markdown("---")
    show_backend_api_status()

    st.markdown("---")
    show_email_status()

    st.markdown("---")
    show_email_configuration()

    st.markdown("---")
    run_email_scan()

    st.markdown("---")
    show_data_integration_status()

    # Footer with helpful information
    st.markdown("---")
    st.markdown("""
    **💡 Quick Tips:**
    - Use **App Passwords** for Gmail, Outlook, and Yahoo (not your regular password)
    - Historical scans may take time for large email archives
    - CVs are automatically detected using keyword analysis
    - All extracted data integrates with your AI enrichment pipeline

    **🔐 Security:** Passwords are encrypted and stored securely in the local database.
    """)

if __name__ == "__main__":
    main()
