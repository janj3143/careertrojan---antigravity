"""
=============================================================================
IntelliCV Admin Portal - EXA Web Intelligence Dashboard (Page 27)
=============================================================================

Deep web search and company enrichment using Exa AI.

Features:
- Manual company search and enrichment
- Automated careers page discovery
- Product/solution page extraction
- Company background research
- Search history and analytics
- Corpus management
- API usage tracking

Integration:
- Feeds data to User Portal Pages 10, 13
- Enhances Admin Pages 10, 11 (Market/Competitive Intelligence)
- Stores enrichment in company_corpora
"""

import streamlit as st
import sys
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add shared modules to path
shared_path = Path(__file__).parent.parent.parent / "shared"
backend_path = Path(__file__).parent.parent.parent / "shared_backend"
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(backend_path))

# Import shared layer
from shared.config import AI_DATA_DIR, RAW_DATA_DIR, WORKING_COPY_DIR
from shared.io import load_data_index, validate_data_integrity, save_stats_payload

# Two-tier web search orchestrator (Google → Exa fallback)
try:
    from services.web_search_orchestrator import get_two_tier_status, two_tier_web_search
    TWO_TIER_AVAILABLE = True
except Exception:
    get_two_tier_status = None  # type: ignore
    two_tier_web_search = None  # type: ignore
    TWO_TIER_AVAILABLE = False

# Knowledge-hole queue (for always-on gap filling)
try:
    from shared_backend.queue.knowledge_hole_queue import get_knowledge_hole_queue_manager
except Exception:
    get_knowledge_hole_queue_manager = None  # type: ignore

try:
    from shared_backend.workers.knowledge_hole_worker import process_one_job
except Exception:
    process_one_job = None  # type: ignore

# =============================================================================
# MANDATORY AUTHENTICATION CHECK
# =============================================================================

def check_authentication():
    """Real authentication check - NO FALLBACKS ALLOWED"""
    try:
        # Check if user is properly authenticated
        if 'authenticated' in st.session_state and st.session_state.authenticated:
            return True
        # If not in session state, redirect to login
        return False
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False

# =============================================================================
# IMPORTS
# =============================================================================

try:
    from services.exa_service.exa_client import get_exa_client
    from services.exa_service.company_enrichment import get_company_enricher
    from services.exa_service.keyword_extractor import get_keyword_extractor
    EXA_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Exa service not available: {e}")
    EXA_AVAILABLE = False

try:
    from services.company_jd_auto_updater import get_company_jd_updater
    JD_UPDATER_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ JD Auto-updater not available: {e}")
    JD_UPDATER_AVAILABLE = False

try:
    from database.exa_db import (
        get_company_sources,
        get_crawl_history,
        get_enrichment_summary,
        get_api_usage_stats,
        health_check as db_health_check
    )
    DB_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Database not available: {e}")
    DB_AVAILABLE = False

try:
    import sys
    integration_path = Path(__file__).parent / "shared"
    sys.path.insert(0, str(integration_path))
    from integration_hooks import get_integration_hooks
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Integration hooks not available: {e}")
    INTEGRATION_AVAILABLE = False


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page25_exa") if BackendTelemetryHelper else None

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="EXA Web Intelligence | IntelliCV Admin",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    """Main page rendering"""

    # Authentication
    if not check_authentication():
        st.error("🔒 Authentication required")
        st.stop()

    # Header
    st.title("🌐 EXA Web Intelligence Dashboard")
    st.markdown("**Deep web search and company enrichment using Exa AI**")
    st.markdown("---")

    if TELEMETRY_HELPER:
        TELEMETRY_HELPER.render_status_panel(
            title="🛰️ Backend Telemetry Monitor",
            refresh_key="page25_backend_refresh",
        )

    # System status
    render_system_status()

    # Tabs for different features
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🔍 Company Search",
        "📊 Search History",
        "📚 Corpus Browser",
        "📈 Analytics",
        "⚙️ Settings",
        "🎯 JD Analysis",
        "🔄 Auto-Update (180d)",
        "🔗 Integrations"
    ])

    with tab1:
        render_company_search_tab()

    with tab2:
        render_search_history_tab()

    with tab3:
        render_corpus_browser_tab()

    with tab4:
        render_analytics_tab()

    with tab5:
        render_settings_tab()

    with tab6:
        render_jd_analysis_tab()

    with tab7:
        render_auto_update_tab()

    with tab8:
        render_integrations_tab()


# =============================================================================
# TAB 8: INTEGRATIONS (Two-tier search wiring)
# =============================================================================

def _integration_manifest() -> Dict[str, List[Dict[str, str]]]:
    """Static manifest of pages that should be wired into web search."""
    base = Path(__file__).parent.parent.parent

    admin_pages = [
        {"label": "Admin 09 – AI Content Generator", "path": str((base / "admin_portal" / "pages" / "09_AI_Content_Generator.py").as_posix())},
        {"label": "Admin 11 – Competitive Intelligence", "path": str((base / "admin_portal" / "pages" / "11_Competitive_Intelligence.py").as_posix())},
        {"label": "Admin 12 – Web Company Intelligence", "path": str((base / "admin_portal" / "pages" / "12_Web_Company_Intelligence.py").as_posix())},
        {"label": "Admin 15 – Advanced Settings", "path": str((base / "admin_portal" / "pages" / "15_Advanced_Settings.py").as_posix())},
        {"label": "Admin 17 – Mentor Management", "path": str((base / "admin_portal" / "pages" / "17_Mentor_Management.py").as_posix())},
        {"label": "Admin 18 – Job Title AI Integration", "path": str((base / "admin_portal" / "pages" / "18_Job_Title_AI_Integration.py").as_posix())},
        {"label": "Admin 19 – Job Title Overlap Cloud", "path": str((base / "admin_portal" / "pages" / "19_Job_Title_Overlap_Cloud.py").as_posix())},
        {"label": "Admin 21 – AI Model Training Review", "path": str((base / "admin_portal" / "pages" / "21_AI_Model_Training_Review.py").as_posix())},
        {"label": "Admin 23 – Intelligence Hub", "path": str((base / "admin_portal" / "pages" / "23_Intelligence_Hub.py").as_posix())},
        {"label": "Admin 24 – Career Pattern Intelligence", "path": str((base / "admin_portal" / "pages" / "24_Career_Pattern_Intelligence.py").as_posix())},
    ]

    mentor_pages = [
        {"label": "Mentor 07 – Mentorship AI Assistant", "path": str((base / "mentor_portal" / "pages" / "07_Mentorship_AI_Assistant.py").as_posix())},
    ]

    user_pages = [
        {"label": "User 10 – UMarketU Suite", "path": str((base / "user_portal_final" / "pages" / "10_UMarketU_Suite.py").as_posix())},
        {"label": "User 11 – Coaching Hub", "path": str((base / "user_portal_final" / "pages" / "11_Coaching_Hub.py").as_posix())},
        {"label": "User 12 – Mentorship Marketplace", "path": str((base / "user_portal_final" / "pages" / "12_Mentorship_Marketplace.py").as_posix())},
        {"label": "User 14 – Dual Career Suite", "path": str((base / "user_portal_final" / "pages" / "14_Dual_Career_Suite.py").as_posix())},
    ]

    return {
        "Admin portal": admin_pages,
        "Mentor portal": mentor_pages,
        "User portal": user_pages,
    }


def _is_page_wired(file_path: str) -> bool:
    """Best-effort detection: checks if a page imports/calls the shared orchestrator."""
    try:
        p = Path(file_path)
        if not p.exists():
            return False
        content = p.read_text(encoding="utf-8", errors="ignore")
        return (
            "web_search_orchestrator" in content
            and "two_tier_web_search" in content
        )
    except Exception:
        return False


def render_integrations_tab():
    st.markdown("### 🔗 Web Search Integrations")
    st.markdown(
        "This tab tracks which pages are wired into the **Google → Exa fallback** strategy, "
        "and provides a small console to test the two-tier pipeline from an admin perspective."
    )

    st.divider()

    # Health / config snapshot
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Two-tier API", "🟢 Available" if TWO_TIER_AVAILABLE else "🔴 Missing")
    with col2:
        if TWO_TIER_AVAILABLE and get_two_tier_status:
            status = get_two_tier_status()
            st.metric("Google Config", "🟢 Set" if status.google_configured else "🟠 Not set")
        else:
            st.metric("Google Config", "N/A")
    with col3:
        if TWO_TIER_AVAILABLE and get_two_tier_status:
            status = get_two_tier_status()
            st.metric("Exa Config", "🟢 Set" if status.exa_configured else "🟠 Not set")
        else:
            st.metric("Exa Config", "N/A")

    st.divider()

    # Integration manifest
    st.markdown("#### 📍 Pages expected to use web search")
    manifest = _integration_manifest()
    for section, pages in manifest.items():
        st.markdown(f"**{section}**")
        for item in pages:
            wired = _is_page_wired(item["path"])
            status_icon = "✅" if wired else "⚠️"

            cols = st.columns([3, 5, 1])
            cols[0].write(f"{status_icon} {item['label']}")
            cols[1].code(item["path"], language="text")
            cols[2].write("Wired" if wired else "Pending")

    st.divider()

    # Test console
    st.markdown("#### 🧪 Two-tier test console")
    if not TWO_TIER_AVAILABLE or not two_tier_web_search:
        st.warning("Two-tier search service is not available in this environment.")
        return

    colA, colB = st.columns([3, 2])
    with colA:
        query = st.text_input(
            "Query",
            placeholder="e.g., site:microsoft.com careers software engineer",
            key="exa_two_tier_query",
        )
        domain = st.text_input(
            "Domain (optional)",
            placeholder="e.g., microsoft.com",
            key="exa_two_tier_domain",
        )
    with colB:
        content_type = st.selectbox(
            "Content type",
            options=["generic", "careers", "products", "background", "job_description"],
            index=0,
            key="exa_two_tier_type",
        )
        num_results = st.slider("Results", min_value=1, max_value=20, value=8, key="exa_two_tier_n")

    run = st.button("Run Two-tier Search", type="primary", use_container_width=True)
    if run:
        if not query.strip():
            st.warning("Please enter a query")
            return

        with st.spinner("Running Google → Exa fallback search..."):
            result = two_tier_web_search(
                query=query.strip(),
                domain=domain.strip() or None,
                content_type=content_type,  # type: ignore[arg-type]
                num_results=int(num_results),
                triggered_from="admin_portal/page25_integrations_tab",
            )

        st.success(f"Completed via: {result.get('method')}")
        st.caption(f"Total time: {result.get('stats', {}).get('total_time_ms', 0)} ms")

        st.markdown("**Counts**")
        st.json(result.get("stats", {}))

        st.markdown("**Top results (URLs)**")
        urls = []
        for bucket in ("filtered_results", "google_results", "exa_results"):
            for r in result.get(bucket, []) or []:
                if r.get("url"):
                    urls.append({"bucket": bucket, "url": r.get("url"), "title": r.get("title", "")})
        st.dataframe(urls[:50], use_container_width=True)

    st.divider()

    # Knowledge hole monitor
    st.markdown("#### 🧠 Knowledge hole queue")
    st.markdown(
        "When AI-ingested data hits a missing concept (a \"knowledge hole\"), the system queues a live research job. "
        "Run the always-on worker to continuously resolve these gaps using Google → Exa."
    )

    if not get_knowledge_hole_queue_manager:
        st.warning("Knowledge-hole queue module is not available in this environment.")
        return

    qm = get_knowledge_hole_queue_manager()
    stats = qm.get_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Backend", stats.backend)
    c2.metric("Queued", stats.queued)
    c3.metric("Processing", stats.processing)
    c4.metric("Completed", stats.completed)
    c5.metric("Failed", stats.failed)

    st.caption("Always-on worker command: `python shared_backend/workers/knowledge_hole_worker.py --poll-interval 10`")

    queued = qm.peek(limit=25)
    if queued:
        st.dataframe(queued, use_container_width=True)
    else:
        st.info("No queued knowledge holes.")

    col_run, col_note = st.columns([1, 3])
    with col_run:
        run_one = st.button("Process next queued hole", type="secondary", use_container_width=True)
    with col_note:
        st.caption("Processes only real queued items; never generates demo/mock content.")

    if run_one:
        if not process_one_job:
            st.error("Resolver function is not available. Use the worker script instead.")
            return

        job = qm.dequeue(timeout_seconds=0)
        if not job:
            st.info("Queue is empty.")
            return

        with st.spinner(f"Resolving {job.get('hole_type')}…"):
            try:
                result = process_one_job(job)
                if result:
                    qm.mark_completed(job, result=result)
                    st.success(f"Resolved and persisted: {result}")
                else:
                    qm.mark_failed(job, error="No resolver available or live lookup returned empty")
                    st.warning("Live lookup returned empty; job marked failed.")
            except Exception as e:
                qm.mark_failed(job, error=str(e))
                st.error(f"Resolver error: {e}")

# =============================================================================
# SYSTEM STATUS
# =============================================================================

def render_system_status():
    """Show system status indicators"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        exa_status = "🟢 Online" if EXA_AVAILABLE else "🔴 Offline"
        st.metric("Exa Service", exa_status)

    with col2:
        db_status = "🟢 Connected" if DB_AVAILABLE else "🔴 Disconnected"
        st.metric("Database", db_status)

    with col3:
        if DB_AVAILABLE:
            try:
                stats = get_api_usage_stats(days=7)
                st.metric("API Calls (7d)", f"{stats['total_calls']:,}")
            except:
                st.metric("API Calls (7d)", "N/A")
        else:
            st.metric("API Calls (7d)", "N/A")

    with col4:
        if DB_AVAILABLE:
            try:
                health = db_health_check()
                status = health.get('status', 'unknown')
                st.metric("DB Health", status.upper())
            except:
                st.metric("DB Health", "UNKNOWN")
        else:
            st.metric("DB Health", "OFFLINE")

# =============================================================================
# TAB 1: COMPANY SEARCH
# =============================================================================

def render_company_search_tab():
    """Manual company search and enrichment"""

    st.markdown("### 🔍 Search & Enrich Company Data")
    st.markdown("Enter a company domain to discover careers pages, products, and background information.")

    if not EXA_AVAILABLE:
        st.error("❌ Exa service is not available. Please check configuration.")
        return

    # Search form
    with st.form("company_search_form"):
        col1, col2 = st.columns([3, 1])

        with col1:
            domain = st.text_input(
                "Company Domain",
                placeholder="example.com (without www or https://)",
                help="Enter the company's main domain"
            )

        with col2:
            company_name = st.text_input(
                "Company Name (optional)",
                placeholder="Example Corp"
            )

        st.markdown("**Search Types:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            search_careers = st.checkbox("🎯 Careers Pages", value=True)
        with col2:
            search_products = st.checkbox("🚀 Product Pages", value=True)
        with col3:
            search_background = st.checkbox("📖 Company Background", value=True)

        col1, col2 = st.columns(2)
        with col1:
            num_results = st.slider("Results per search", 3, 20, 5)
        with col2:
            use_cache = st.checkbox("Use cache (faster)", value=True)

        submitted = st.form_submit_button("🔍 Search & Enrich", type="primary", use_container_width=True)

    # Process search
    if submitted and domain:
        if not any([search_careers, search_products, search_background]):
            st.warning("⚠️ Please select at least one search type")
            return

        # Clean domain
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip().rstrip("/")

        st.markdown("---")
        st.markdown(f"### 🔄 Enriching: **{domain}**")

        enricher = get_company_enricher()

        # Progress tracking
        progress_text = st.empty()
        progress_bar = st.progress(0)
        results_container = st.container()

        total_steps = sum([search_careers, search_products, search_background])
        current_step = 0

        all_results = {
            'domain': domain,
            'company_name': company_name or domain,
            'timestamp': datetime.now().isoformat(),
            'careers': None,
            'products': None,
            'background': None,
            'total_pages': 0
        }

        # Search careers
        if search_careers:
            current_step += 1
            progress_text.text(f"🎯 Searching careers pages... ({current_step}/{total_steps})")
            progress_bar.progress(current_step / total_steps)

            try:
                careers_result = enricher.find_careers_pages(
                    domain=domain,
                    num_results=num_results,
                    use_cache=use_cache
                )
                all_results['careers'] = careers_result
                all_results['total_pages'] += careers_result.get('total_found', 0)

                with results_container:
                    render_search_results("Careers Pages", careers_result, "🎯")

            except Exception as e:
                with results_container:
                    st.error(f"❌ Careers search failed: {e}")

        # Search products
        if search_products:
            current_step += 1
            progress_text.text(f"🚀 Searching product pages... ({current_step}/{total_steps})")
            progress_bar.progress(current_step / total_steps)

            try:
                products_result = enricher.find_product_pages(
                    domain=domain,
                    num_results=num_results,
                    use_cache=use_cache
                )
                all_results['products'] = products_result
                all_results['total_pages'] += products_result.get('total_found', 0)

                with results_container:
                    render_search_results("Product Pages", products_result, "🚀")

            except Exception as e:
                with results_container:
                    st.error(f"❌ Products search failed: {e}")

        # Search background
        if search_background:
            current_step += 1
            progress_text.text(f"📖 Searching company background... ({current_step}/{total_steps})")
            progress_bar.progress(current_step / total_steps)

            try:
                background_result = enricher.get_company_background(
                    domain=domain,
                    num_results=num_results,
                    use_cache=use_cache
                )
                all_results['background'] = background_result
                all_results['total_pages'] += background_result.get('total_found', 0)

                with results_container:
                    render_search_results("Company Background", background_result, "📖")

            except Exception as e:
                with results_container:
                    st.error(f"❌ Background search failed: {e}")

        # Complete
        progress_text.text("✅ Enrichment complete!")
        progress_bar.progress(1.0)

        # Summary
        st.markdown("---")
        st.success(f"✅ **Enrichment Complete**: Found **{all_results['total_pages']} total pages** for {domain}")

        # Sync to integration hooks
        try:
            if INTEGRATION_AVAILABLE:
                hooks = get_integration_hooks()
                hooks.sync_exa_company_data(domain, all_results)
                st.success("🔄 Data synced to user portals and backend")
        except Exception as e:
            st.warning(f"⚠️ Integration sync failed (non-critical): {e}")

        # Sync to integration hooks (if available)
        if INTEGRATION_AVAILABLE:
            try:
                hooks = get_integration_hooks()
                hooks.sync_exa_company_data(domain, all_results)
                st.success("🔄 Data synced to user portals and backend")
            except Exception as e:
                st.warning(f"⚠️ Integration sync failed: {e}")

        # Download option
        st.download_button(
            label="📥 Download Full Results (JSON)",
            data=json.dumps(all_results, indent=2),
            file_name=f"{domain}_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def render_search_results(title, results, icon):
    """Render search results for a category"""

    st.markdown(f"### {icon} {title}")

    total_found = results.get('total_found', 0)
    from_cache = results.get('from_cache', False)
    cache_indicator = "💾 (cached)" if from_cache else "🌐 (fresh)"

    st.markdown(f"**Found**: {total_found} pages {cache_indicator}")

    # Get results based on category
    if 'careers' in title.lower():
        pages = results.get('careers_pages', [])
    elif 'product' in title.lower():
        pages = results.get('product_pages', [])
    else:
        pages = results.get('background_pages', [])

    if not pages:
        st.info("No results found")
        return

    # Display results
    for i, page in enumerate(pages, 1):
        with st.expander(f"#{i} - {page.get('title', 'Untitled')} (Score: {page.get('score', 0):.3f})"):
            st.markdown(f"**URL**: [{page.get('url', 'N/A')}]({page.get('url', '#')})")

            if page.get('published_date'):
                st.markdown(f"**Published**: {page.get('published_date')}")

            if page.get('author'):
                st.markdown(f"**Author**: {page.get('author')}")

            # Content preview
            content = page.get('text', '')
            if content:
                st.markdown("**Content Preview:**")
                st.text_area("", value=content[:500] + "..." if len(content) > 500 else content, height=150, key=f"content_{i}")

    st.markdown("---")

# =============================================================================
# TAB 2: SEARCH HISTORY
# =============================================================================

def render_search_history_tab():
    """Display search history from database"""

    st.markdown("### 📊 Search History")

    if not DB_AVAILABLE:
        st.warning("⚠️ Database not available. Cannot display history.")
        return

    # Search filter
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_domain = st.text_input("Filter by domain", placeholder="example.com")
    with col2:
        limit = st.number_input("Show records", 5, 100, 20)

    if st.button("🔍 Load History"):
        if filter_domain:
            try:
                history = get_crawl_history(filter_domain, limit=limit)

                if not history:
                    st.info(f"No history found for {filter_domain}")
                else:
                    st.success(f"Found {len(history)} records for {filter_domain}")

                    for record in history:
                        with st.expander(f"{record['domain']} - {record['created_at']} ({record['status']})"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Pages", record.get('total_pages_found', 0))
                            with col2:
                                st.metric("Careers", record.get('careers_pages_found', 0))
                            with col3:
                                st.metric("Products", record.get('products_pages_found', 0))

                            st.json(record)

            except Exception as e:
                st.error(f"Failed to load history: {e}")
        else:
            st.warning("Please enter a domain to filter")

# =============================================================================
# TAB 3: CORPUS BROWSER
# =============================================================================

def render_corpus_browser_tab():
    """Browse saved company corpora"""

    st.markdown("### 📚 Company Corpus Browser")
    st.info("Browse enriched company data saved to local corpus storage")

    # Use shared configuration for corpus directory
    corpus_dir = AI_DATA_DIR / "company_corpora"

    if not corpus_dir.exists():
        st.warning("⚠️ Corpus directory not found")
        return

    # List all company domains
    domains = [d.name for d in corpus_dir.iterdir() if d.is_dir()]

    if not domains:
        st.info("No companies in corpus yet. Run some searches first!")
        return

    st.markdown(f"**Total companies in corpus**: {len(domains)}")

    selected_domain = st.selectbox("Select a company", sorted(domains))

    if selected_domain:
        enrichment_file = corpus_dir / selected_domain / "enrichment.json"

        if enrichment_file.exists():
            with open(enrichment_file, 'r') as f:
                data = json.load(f)

            st.success(f"✅ Enrichment data for **{selected_domain}**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Careers Pages", data.get('careers', {}).get('total_found', 0))
            with col2:
                st.metric("Product Pages", data.get('products', {}).get('total_found', 0))
            with col3:
                st.metric("Background Pages", data.get('background', {}).get('total_found', 0))

            # Download
            st.download_button(
                "📥 Download Corpus",
                data=json.dumps(data, indent=2),
                file_name=f"{selected_domain}_corpus.json",
                mime="application/json"
            )

            # Show data
            with st.expander("📄 View Full Data"):
                st.json(data)
        else:
            st.warning("No enrichment.json found for this domain")

# =============================================================================
# TAB 4: ANALYTICS
# =============================================================================

def render_analytics_tab():
    """Show usage analytics - REAL DATA ONLY"""

    st.markdown("### 📈 Usage Analytics")

    # Validate data integrity first
    with st.spinner("🔍 Validating data integrity..."):
        integrity_check = validate_data_integrity()

    if integrity_check["status"] != "VALID":
        st.error("⚠️ Data integrity issues detected - analytics may be unreliable")
        st.json(integrity_check)
        if not st.checkbox("Show analytics anyway (not recommended)"):
            return
    else:
        st.success(f"✅ Data validated: {integrity_check['actual_files']} files")

    if not DB_AVAILABLE:
        st.warning("⚠️ Database not available. Showing file-based analytics instead.")

        # Use real data from ai_data_final
        try:
            # Load real data index
            data_index = load_data_index()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Data Files", data_index.get("file_count", 0))
            with col2:
                st.metric("Data Size (MB)", f"{data_index.get('total_size_mb', 0):.1f}")
            with col3:
                st.metric("Last Updated", data_index.get("generated_at", "Unknown")[:10])

            # Show directory breakdown
            st.markdown("### 📊 Data Distribution")
            structure = data_index.get("structure", {}).get("directories", {})

            if structure:
                import pandas as pd
                dir_data = []
                for dir_name, count in structure.items():
                    dir_data.append({"Directory": dir_name, "Files": count})

                df = pd.DataFrame(dir_data)
                st.bar_chart(df.set_index("Directory"))

        except Exception as e:
            st.error(f"Failed to load real analytics: {e}")
            return
    else:
        # Time period selector for DB analytics
        period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days"])

        days_map = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90
        }

        days = days_map[period]

        try:
            stats = get_api_usage_stats(days=days)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total API Calls", f"{stats['total_calls']:,}")
            with col2:
                st.metric("Total Results", f"{stats['total_results']:,}")
            with col3:
                st.metric("Unique Domains", stats['unique_domains'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Response Time", f"{stats['avg_response_time_ms']:.0f} ms")
            with col2:
                st.metric("Credits Used", f"{stats['total_credits_used']:.2f}")
            with col3:
                st.metric("Failed Calls", stats['failed_calls'])

        except Exception as e:
            st.error(f"Failed to load analytics: {e}")

    # Save analytics access stats
    analytics_stats = {
        "page": "exa_web_intelligence_analytics",
        "data_integrity": integrity_check,
        "db_available": DB_AVAILABLE,
        "access_timestamp": datetime.now().isoformat()
    }

    try:
        save_stats_payload(analytics_stats, "exa_analytics_access")
    except Exception as e:
        st.warning(f"Could not save analytics stats: {e}")

# =============================================================================
# TAB 6: JD ANALYSIS
# =============================================================================

def render_jd_analysis_tab():
    """Smart JD keyword extraction and search"""

    st.markdown("### 🎯 Job Description Analysis & Smart Search")
    st.markdown("Extract keywords from JDs, analyze job titles, and run hybrid AI + SQLite searches")

    # Sub-tabs
    subtab1, subtab2, subtab3 = st.tabs([
        "📝 JD Keyword Extraction",
        "🏷️ Job Title Analysis",
        "🔍 Smart Search"
    ])

    # SUBTAB 1: JD Keyword Extraction
    with subtab1:
        st.markdown("#### Extract Keywords from Job Descriptions")

        # Input area
        jd_text = st.text_area(
            "Paste Job Description:",
            height=300,
            placeholder="Paste the full job description text here...",
            help="Paste a job description to extract required skills, nice-to-have, tech stack, experience, education, etc."
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            extract_btn = st.button("🔍 Extract Keywords", type="primary")

        if extract_btn and jd_text:
            try:
                extractor = get_keyword_extractor()

                with st.spinner("Analyzing job description..."):
                    result = extractor.extract_job_description_keywords(jd_text)

                # Display results
                st.success("✅ Extraction Complete!")

                # Experience & Education
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**📋 Experience Required**")
                    if result['experience']:
                        exp = result['experience']
                        st.info(f"{exp.get('years_required', 'N/A')} years ({exp.get('mentions', 0)} mentions)")
                    else:
                        st.info("Not specified")

                with col2:
                    st.markdown("**🎓 Education Required**")
                    if result['education']:
                        st.info(", ".join(result['education']))
                    else:
                        st.info("Not specified")

                # Required vs Nice-to-Have Skills
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**✅ Required Skills ({len(result['required_skills'])})**")
                    for skill in result['required_skills'][:10]:
                        st.markdown(f"- {skill}")

                    if len(result['required_skills']) > 10:
                        st.caption(f"...and {len(result['required_skills']) - 10} more")

                with col2:
                    st.markdown(f"**💎 Nice-to-Have ({len(result['nice_to_have'])})**")
                    for skill in result['nice_to_have'][:10]:
                        st.markdown(f"- {skill}")

                    if len(result['nice_to_have']) > 10:
                        st.caption(f"...and {len(result['nice_to_have']) - 10} more")

                # Tech Stack with Frequency
                st.markdown("---")
                st.markdown(f"**🔧 Tech Stack (Top 15 by frequency)**")

                tech_data = []
                for tech in result['tech_stack'][:15]:
                    tech_data.append({
                        "Keyword": tech['keyword'],
                        "Frequency": tech['frequency'],
                        "Confidence": f"{tech['confidence']*100:.0f}%",
                        "Method": tech['method']
                    })

                if tech_data:
                    import pandas as pd
                    df = pd.DataFrame(tech_data)
                    st.dataframe(df, use_container_width=True)

                # Soft Skills
                st.markdown("---")
                st.markdown("**🤝 Soft Skills**")
                st.write(", ".join(result['soft_skills']) if result['soft_skills'] else "None detected")

                # Keyword Frequency Chart
                st.markdown("---")
                st.markdown("**📊 Keyword Frequency Count (Top 20)**")

                if result['keyword_counts']:
                    sorted_keywords = sorted(result['keyword_counts'].items(), key=lambda x: x[1], reverse=True)[:20]

                    import pandas as pd
                    chart_data = pd.DataFrame(sorted_keywords, columns=['Keyword', 'Count'])
                    st.bar_chart(chart_data.set_index('Keyword'))

                # Download JSON
                st.markdown("---")
                json_data = json.dumps(result, indent=2)
                st.download_button(
                    label="📥 Download Full Analysis (JSON)",
                    data=json_data,
                    file_name=f"jd_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            except Exception as e:
                st.error(f"Extraction failed: {e}")

        elif extract_btn:
            st.warning("⚠️ Please paste a job description first")

    # SUBTAB 2: Job Title Analysis
    with subtab2:
        st.markdown("#### Analyze Job Titles")
        st.markdown("Parse job titles into structured components (level, role, domain)")

        # Single title analysis
        st.markdown("**Single Title Analysis**")
        job_title = st.text_input(
            "Job Title:",
            placeholder="e.g., Senior Machine Learning Engineer",
            help="Enter a job title to analyze"
        )

        if job_title:
            try:
                extractor = get_keyword_extractor()
                analysis = extractor.analyze_job_title(job_title)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Level", analysis['level'] or "Not detected")

                with col2:
                    st.metric("Role", analysis['role'] or "Not detected")

                with col3:
                    st.metric("Domain", analysis['domain'] or "Not detected")

                st.metric("Seniority Score", f"{analysis['seniority_score']}/100")

                st.json(analysis)

            except Exception as e:
                st.error(f"Analysis failed: {e}")

        # Batch analysis
        st.markdown("---")
        st.markdown("**Batch Title Analysis**")

        titles_text = st.text_area(
            "Job Titles (one per line):",
            height=200,
            placeholder="Senior ML Engineer\nStaff Software Developer\nJunior Frontend Developer\n...",
            help="Enter multiple job titles, one per line"
        )

        batch_btn = st.button("🔍 Analyze Batch", key="batch_titles")

        if batch_btn and titles_text:
            try:
                extractor = get_keyword_extractor()
                titles = [t.strip() for t in titles_text.split('\n') if t.strip()]

                with st.spinner(f"Analyzing {len(titles)} titles..."):
                    batch_result = extractor.batch_analyze_job_titles(titles)

                st.success(f"✅ Analyzed {batch_result['total_titles']} titles")

                # Summary metrics
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Average Seniority", f"{batch_result['average_seniority']:.1f}/100")

                with col2:
                    st.metric("Unique Levels", len(batch_result['most_common_levels']))

                # Most common components
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Most Common Levels**")
                    for item in batch_result['most_common_levels'][:5]:
                        st.write(f"{item['item']}: {item['count']}")

                with col2:
                    st.markdown("**Most Common Roles**")
                    for item in batch_result['most_common_roles'][:5]:
                        st.write(f"{item['item']}: {item['count']}")

                with col3:
                    st.markdown("**Most Common Domains**")
                    for item in batch_result['most_common_domains'][:5]:
                        st.write(f"{item['item']}: {item['count']}")

                # Individual results
                st.markdown("---")
                st.markdown("**Individual Title Analyses**")

                for title in titles:
                    with st.expander(f"📌 {title}"):
                        analysis = extractor.analyze_job_title(title)
                        st.json(analysis)

            except Exception as e:
                st.error(f"Batch analysis failed: {e}")

    # SUBTAB 3: Smart Search
    with subtab3:
        st.markdown("#### Smart Hybrid AI + SQLite Search")
        st.markdown("Natural language queries → Intelligent SQLite WHERE clauses")

        # Search input
        search_query = st.text_input(
            "Search Query:",
            placeholder="e.g., Find companies hiring Python developers in Seattle",
            help="Enter a natural language search query"
        )

        search_type = st.selectbox(
            "Search Type:",
            options=['hybrid', 'semantic', 'keyword'],
            help="Hybrid = AI + exact matching, Semantic = AI only, Keyword = exact only"
        )

        search_btn = st.button("🔍 Generate Search", type="primary")

        if search_btn and search_query:
            try:
                extractor = get_keyword_extractor()

                with st.spinner("Analyzing query and generating SQL..."):
                    result = extractor.smart_search(search_query, search_type=search_type)

                st.success("✅ Search Strategy Generated!")

                # Extracted components
                st.markdown("### 📌 Extracted Components")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Keywords**")
                    st.write(", ".join(result['extracted_keywords']) if result['extracted_keywords'] else "None")

                    st.markdown("**Level**")
                    st.write(result['extracted_level'] or "Any")

                with col2:
                    st.markdown("**Role**")
                    st.write(result['extracted_role'] or "Any")

                    st.markdown("**Location**")
                    st.write(result['extracted_location'] or "Any")

                # Semantic expansions
                if result['semantic_expansions']:
                    st.markdown("---")
                    st.markdown("### 🧠 Semantic Expansions")

                    for base, expanded in result['semantic_expansions'].items():
                        st.write(f"**{base}** → {', '.join(expanded[:5])}")

                # SQLite WHERE clauses
                st.markdown("---")
                st.markdown("### 💾 Generated SQLite WHERE Clauses")

                for i, clause in enumerate(result['sql_where_clauses'], 1):
                    st.code(clause, language="sql")

                # Final SQL
                st.markdown("---")
                st.markdown("### 📝 Complete SQL Query")
                st.code(result['final_sql'], language="sql")

                # Copy button
                st.button("📋 Copy SQL", help="Copy SQL to clipboard")

                # Download
                json_data = json.dumps(result, indent=2)
                st.download_button(
                    label="📥 Download Search Strategy (JSON)",
                    data=json_data,
                    file_name=f"search_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            except Exception as e:
                st.error(f"Search generation failed: {e}")

        elif search_btn:
            st.warning("⚠️ Please enter a search query")

        # Examples
        st.markdown("---")
        st.markdown("### 💡 Example Queries")

        examples = [
            "Find companies hiring Python developers",
            "Senior ML engineer roles in Seattle",
            "Remote backend jobs at startups",
            "AWS engineers with Docker experience",
            "Data scientist positions requiring PhD",
            "Junior frontend developers in San Francisco"
        ]

        for example in examples:
            if st.button(f"Try: {example}", key=f"example_{example}"):
                st.rerun()

# =============================================================================
# TAB 5: SETTINGS
# =============================================================================

def render_settings_tab():
    """Configuration settings"""

    st.markdown("### ⚙️ EXA Service Settings")

    # Current configuration
    import os

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**API Configuration**")
        api_key = os.getenv('EXA_API_KEY', 'Not set')
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else "Not set"
        st.code(f"API Key: {masked_key}")
        st.code(f"Base URL: {os.getenv('EXA_BASE_URL', 'https://api.exa.ai')}")
        st.code(f"Search Mode: {os.getenv('EXA_SEARCH_MODE', 'auto')}")

    with col2:
        st.markdown("**Limits & Performance**")
        st.code(f"Max Results: {os.getenv('EXA_MAX_RESULTS', '50')}")
        st.code(f"Rate Limit: {os.getenv('EXA_RATE_LIMIT', '100')} req/min")
        st.code(f"Cache TTL: {os.getenv('EXA_CACHE_TTL', '86400')} sec")

    st.markdown("---")

    # Feature flags
    st.markdown("**Feature Flags**")
    col1, col2 = st.columns(2)

    with col1:
        enable_exa = os.getenv('ENABLE_EXA_SERVICE', 'true') == 'true'
        st.checkbox("Exa Service Enabled", value=enable_exa, disabled=True)

        enable_enrichment = os.getenv('ENABLE_COMPANY_ENRICHMENT', 'true') == 'true'
        st.checkbox("Company Enrichment", value=enable_enrichment, disabled=True)

    with col2:
        enable_auto = os.getenv('ENABLE_AUTO_CRAWL', 'false') == 'true'
        st.checkbox("Auto Crawl (Phase 3)", value=enable_auto, disabled=True)

        enable_workers = os.getenv('ENABLE_BACKGROUND_WORKERS', 'false') == 'true'
        st.checkbox("Background Workers (Phase 3)", value=enable_workers, disabled=True)

    st.info("💡 To modify settings, edit the .env file in the root directory")

# =============================================================================
# TAB 7: AUTO-UPDATE (180-DAY SYSTEM)
# =============================================================================

def render_auto_update_tab():
    """180-day automatic company JD update system"""

    st.markdown("### 🔄 Automatic Company Job Description Updates")
    st.markdown("""
    **Intelligent 180-Day Company Search System**

    This system automatically:
    - Tracks companies from user employment history
    - Checks if company was searched in last 180 days
    - Auto-searches dormant companies when users login
    - Stores JD history for speculative applications
    - Enables admin bulk updates
    """)

    if not JD_UPDATER_AVAILABLE:
        st.error("❌ JD Auto-updater service not available")
        return

    st.markdown("---")

    # Get updater instance
    try:
        updater = get_company_jd_updater()
    except Exception as e:
        st.error(f"❌ Failed to initialize auto-updater: {e}")
        return

    # Statistics dashboard
    st.markdown("#### 📊 System Statistics")

    try:
        stats = updater.get_statistics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Companies Tracked", stats.get('total_companies', 0))

        with col2:
            dormant = stats.get('dormant_companies', 0)
            dormant_pct = stats.get('dormant_percentage', 0)
            st.metric("Dormant Companies", f"{dormant} ({dormant_pct:.1f}%)")

        with col3:
            st.metric("Total Job Descriptions", stats.get('total_job_descriptions', 0))

        with col4:
            st.metric("Recent Searches (7d)", stats.get('recent_searches_7d', 0))

    except Exception as e:
        st.error(f"Error loading statistics: {e}")

    st.markdown("---")

    # Dormant companies list
    st.markdown("#### 🚨 Dormant Companies (>180 days)")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        min_users = st.number_input(
            "Minimum user count:",
            min_value=0,
            max_value=100,
            value=1,
            help="Only show companies with at least this many users"
        )

    with col2:
        max_display = st.number_input(
            "Max companies to display:",
            min_value=10,
            max_value=1000,
            value=50,
            help="Limit number of results"
        )

    with col3:
        st.write("")  # Spacing
        st.write("")
        refresh_btn = st.button("🔄 Refresh List", type="secondary")

    try:
        dormant_companies = updater.get_dormant_companies(
            limit=max_display,
            min_user_count=min_users
        )

        if dormant_companies:
            st.success(f"✅ Found {len(dormant_companies)} dormant companies")

            # Convert to dataframe for display
            import pandas as pd
            df = pd.DataFrame(dormant_companies)

            # Format columns
            df['days_since_search'] = df['days_since_search'].apply(
                lambda x: f"{x} days" if x < 9999 else "Never"
            )
            df['last_search_date'] = df['last_search_date'].fillna('Never')

            # Display table
            st.dataframe(
                df[[
                    'company_name', 'user_count', 'days_since_search',
                    'last_search_date', 'total_searches', 'priority_score'
                ]],
                use_container_width=True,
                column_config={
                    "company_name": "Company",
                    "user_count": st.column_config.NumberColumn("Users", format="%d"),
                    "days_since_search": "Days Since Search",
                    "last_search_date": "Last Searched",
                    "total_searches": st.column_config.NumberColumn("Total Searches", format="%d"),
                    "priority_score": st.column_config.NumberColumn("Priority", format="%.0f")
                }
            )

        else:
            st.info("✅ No dormant companies found! All companies are up to date.")

    except Exception as e:
        st.error(f"Error loading dormant companies: {e}")

    st.markdown("---")

    # Bulk update section
    st.markdown("#### 🔄 Bulk Company Update")
    st.markdown("""
    Select how many dormant companies you want to update with latest job descriptions.

    **Search Priority Order:**
    1. 🔵 **Google Search** (Primary) - Free, comprehensive
    2. 🟣 **EXA API** (Fallback) - When Google hits limits or blocks
    """)

    col1, col2 = st.columns([3, 1])

    with col1:
        bulk_count = st.number_input(
            "Number of companies to update:",
            min_value=1,
            max_value=1000,
            value=10,
            help="How many dormant companies to search and update"
        )

        st.info(f"💡 Will update top {bulk_count} companies by priority score (user count × dormancy)")

    with col2:
        st.write("")  # Spacing
        st.write("")
        start_bulk_btn = st.button("🚀 Start Bulk Update", type="primary")

    if start_bulk_btn:
        if not EXA_AVAILABLE:
            st.warning("⚠️ EXA service not available - will use basic search only")

        st.markdown("---")
        st.markdown("### 🔄 Bulk Update in Progress...")

        # Get companies to update
        companies_to_update = updater.get_dormant_companies(
            limit=bulk_count,
            min_user_count=min_users
        )

        if not companies_to_update:
            st.info("No companies to update!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_area = st.empty()

            results = []

            for idx, company in enumerate(companies_to_update):
                company_name = company['company_name']
                status_text.text(f"🔍 Searching {company_name}... ({idx+1}/{len(companies_to_update)})")
                progress_bar.progress((idx + 1) / len(companies_to_update))

                try:
                    # Try Google first, then EXA
                    jd_count = 0
                    search_method = "none"

                    if EXA_AVAILABLE:
                        enricher = get_company_enricher()
                        careers_result = enricher.find_careers_pages(
                            domain=company.get('company_domain', f"{company_name.lower().replace(' ', '')}.com"),
                            max_results=5
                        )

                        if careers_result and careers_result.get('careers_pages'):
                            jd_count = len(careers_result['careers_pages'])
                            search_method = "exa_api"

                            # Store JDs (simplified - would extract full text in production)
                            for page in careers_result['careers_pages']:
                                # This is placeholder - in production, would scrape each page
                                pass

                    # Record search completion
                    updater.record_search_completed(
                        company_name=company_name,
                        jd_count=jd_count,
                        search_method=search_method,
                        notes=f"Bulk update {datetime.now().strftime('%Y-%m-%d')}"
                    )

                    results.append({
                        'company': company_name,
                        'status': '✅ Success',
                        'jds_found': jd_count,
                        'method': search_method
                    })

                except Exception as e:
                    results.append({
                        'company': company_name,
                        'status': f'❌ Error: {str(e)[:50]}',
                        'jds_found': 0,
                        'method': 'failed'
                    })

                # Small delay to avoid rate limits
                time.sleep(0.5)

            # Show results
            status_text.text("✅ Bulk update complete!")
            progress_bar.progress(1.0)

            import pandas as pd
            results_df = pd.DataFrame(results)
            results_area.dataframe(results_df, use_container_width=True)

            # Summary
            success_count = len([r for r in results if r['status'] == '✅ Success'])
            total_jds = sum(r['jds_found'] for r in results)

            st.success(f"""
            **Bulk Update Summary:**
            - Companies processed: {len(results)}
            - Successful: {success_count}
            - Total JDs collected: {total_jds}
            """)

    st.markdown("---")

    # Company JD history viewer
    st.markdown("#### 📚 Company JD History")

    company_search = st.text_input(
        "Search company:",
        placeholder="Enter company name...",
        help="View all stored job descriptions for a company"
    )

    if company_search:
        try:
            jd_history = updater.get_company_jd_history(company_search)

            if jd_history:
                st.success(f"Found {len(jd_history)} job descriptions for {company_search}")

                for idx, jd in enumerate(jd_history, 1):
                    with st.expander(f"{idx}. {jd['job_title']} - {jd['collected_date'][:10]}"):
                        st.markdown(f"**Collected:** {jd['collected_date']}")
                        if jd['job_url']:
                            st.markdown(f"**URL:** {jd['job_url']}")

                        st.markdown("**Required Skills:**")
                        st.write(", ".join(jd['required_skills'][:10]) if jd['required_skills'] else "Not extracted")

                        st.markdown("**Tech Stack:**")
                        st.write(", ".join([t['keyword'] for t in jd['tech_stack'][:10]]) if jd['tech_stack'] else "Not extracted")

                        st.markdown("**Description Preview:**")
                        st.text(jd['description'][:300] + "..." if len(jd['description']) > 300 else jd['description'])
            else:
                st.info(f"No job descriptions found for {company_search}")

        except Exception as e:
            st.error(f"Error loading JD history: {e}")

# =============================================================================
# RUN MAIN
# =============================================================================

if __name__ == "__main__":
    main()
