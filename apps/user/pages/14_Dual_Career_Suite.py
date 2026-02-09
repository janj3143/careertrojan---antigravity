"""
💑 Dual Career Suite - Partner Career Optimization
==================================================
Upload both partner profiles and optimize dual job search
with geographic feasibility and travel distance analysis.

PREMIUM FEATURE - Annual Pro Tier ($149.99/year)
Cost: 12 tokens per dual analysis
"""

import hashlib
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# Add parent directory to path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Shared backend services (Complete Data Parser + EXA + market intelligence)
try:
    from shared_backend.services.portal_bridge import ResumeService, IntelligenceService
except ImportError:
    ResumeService = None  # type: ignore
    IntelligenceService = None  # type: ignore

try:
    RESUME_SERVICE = ResumeService() if ResumeService else None
    RESUME_SERVICE_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - diagnostic path
    RESUME_SERVICE = None
    RESUME_SERVICE_ERROR = str(exc)

try:
    INTELLIGENCE_SERVICE = IntelligenceService() if IntelligenceService else None
    INTELLIGENCE_SERVICE_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - diagnostic path
    INTELLIGENCE_SERVICE = None
    INTELLIGENCE_SERVICE_ERROR = str(exc)

try:
    from shared_backend.services.exa_service import get_exa_client

    EXA_CLIENT = get_exa_client()
    EXA_AVAILABLE = True
    EXA_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - diagnostic path
    EXA_CLIENT = None
    EXA_AVAILABLE = False
    EXA_ERROR = str(exc)

try:
    from shared_backend.services.web_search_orchestrator import two_tier_web_search  # type: ignore

    TWO_TIER_AVAILABLE = True
    TWO_TIER_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - diagnostic path
    two_tier_web_search = None  # type: ignore
    TWO_TIER_AVAILABLE = False
    TWO_TIER_ERROR = str(exc)


def parse_location_preferences(raw_value: str) -> List[str]:
    """Split comma-separated locations into normalized list."""
    if not raw_value:
        return []
    return [entry.strip() for entry in raw_value.split(",") if entry.strip()]


def _extract_primary_role(career_goals: str, parsed_resume: Optional[Dict[str, Any]]) -> str:
    """Best-effort role hint pulled from user input or parsed resume."""
    if career_goals:
        return career_goals.split("\n", 1)[0].strip()
    if parsed_resume:
        for key in ("headline", "current_role", "title", "summary"):
            value = parsed_resume.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _extract_skills(parsed_resume: Optional[Dict[str, Any]]) -> List[str]:
    """Pull skill arrays from parsed resume payload."""
    if not parsed_resume:
        return []
    skill_sources: List[List[str]] = []
    if isinstance(parsed_resume.get("skills"), list):
        skill_sources.append(parsed_resume["skills"])
    metadata = parsed_resume.get("metadata", {}) if isinstance(parsed_resume.get("metadata"), dict) else {}
    if isinstance(metadata.get("skills"), list):
        skill_sources.append(metadata["skills"])
    real_ai = parsed_resume.get("real_ai_analysis", {}) if isinstance(parsed_resume.get("real_ai_analysis"), dict) else {}
    if isinstance(real_ai.get("real_skills_found"), list):
        skill_sources.append(real_ai["real_skills_found"])
    skills: List[str] = []
    seen = set()
    for source in skill_sources:
        for skill in source:
            if isinstance(skill, str):
                normalized = skill.strip()
                if normalized and normalized.lower() not in seen:
                    seen.add(normalized.lower())
                    skills.append(normalized)
    return skills


def _convert_distance_to_km(value: float, unit: str) -> float:
    return value if unit == "Kilometers" else value * 1.60934


def _convert_distance_from_km(value: float, unit: str) -> float:
    return value if unit == "Kilometers" else value / 1.60934


def _format_currency(amount: float) -> str:
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount/1_000:.0f}K"
    return f"${amount:,.0f}"


def _format_range(range_tuple: Tuple[int, int]) -> str:
    low, high = range_tuple
    return f"{_format_currency(low)} – {_format_currency(high)}" if high else _format_currency(low)


def _get_partner_profile(
    *,
    name: str,
    career_goals: str,
    location_text: str,
    salary_range: Tuple[int, int],
    parsed_resume: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "name": name.strip(),
        "career_goals": career_goals.strip(),
        "locations": parse_location_preferences(location_text),
        "salary_range": salary_range,
        "parsed_resume": parsed_resume,
        "skills": _extract_skills(parsed_resume),
        "role_hint": _extract_primary_role(career_goals, parsed_resume),
    }


def _market_signal(partner_profile: Dict[str, Any], location: str) -> Dict[str, Any]:
    """Blend Complete Data Parser output with market intel + EXA."""
    role_hint = partner_profile.get("role_hint") or "Generalist"
    skills = partner_profile.get("skills", [])
    intel_payload: Dict[str, Any] = {}
    keyword_count = 0

    if INTELLIGENCE_SERVICE:
        try:
            intel_payload = INTELLIGENCE_SERVICE.get_market_intelligence(role_hint, location)
            keyword_count = intel_payload.get("keyword_count") or len(intel_payload.get("ats_keywords", []))
        except Exception as exc:  # pragma: no cover - diagnostic path
            intel_payload = {"status": "failed", "error": str(exc)}

    base_signal = len(skills) * 2 + (keyword_count * 3)
    if partner_profile["salary_range"][1] > 0:
        spread = (partner_profile["salary_range"][1] - partner_profile["salary_range"][0]) / 100_000
        base_signal += max(0, 5 - spread)

    return {
        "job_estimate": max(5, int(base_signal)),
        "keyword_signal": keyword_count,
        "intel": intel_payload,
        "role_hint": role_hint,
        "skills": skills,
    }


def _estimate_commute(commute_band_km: Tuple[int, int], p1_signal: Dict[str, Any], p2_signal: Dict[str, Any]) -> int:
    min_pref, max_pref = commute_band_km
    if max_pref == 0:
        return 0
    keyword_mass = p1_signal.get("keyword_signal", 0) + p2_signal.get("keyword_signal", 0)
    reduction = min(max_pref * 0.6, keyword_mass * 1.5)
    estimate = max(min_pref, int(max_pref - reduction))
    return estimate


def _fetch_exa_insight(location: str, role_hint: str) -> Optional[Dict[str, str]]:
    query = f"{location} {role_hint or 'job market'} hiring outlook 2025"

    # Prefer the platform-wide Google-first → Exa fallback strategy.
    if TWO_TIER_AVAILABLE and two_tier_web_search:
        try:
            payload = two_tier_web_search(
                query=query,
                content_type="generic",
                num_results=1,
                triggered_from="user_portal_final.pages.14_Dual_Career_Suite._fetch_exa_insight",
            )
            candidates = (payload.get("exa_results") or []) + (payload.get("google_results") or [])
            top = (candidates or [None])[0]
            if not top:
                return None
            return {
                "title": top.get("title", ""),
                "url": top.get("url", ""),
                "source": payload.get("method", "two_tier"),
            }
        except Exception:
            pass

    # Fallback: direct Exa client (legacy path).
    if not EXA_AVAILABLE or not EXA_CLIENT:
        return None
    try:
        payload = EXA_CLIENT.search(query, num_results=1, include_content=False, use_autoprompt=True)
        top_result = (payload.get("results") or [None])[0]
        if not top_result:
            return None
        return {
            "title": top_result.get("title", ""),
            "url": top_result.get("url", ""),
            "source": payload.get("_metadata", {}).get("query", query)
        }
    except Exception:
        return None


def _run_dual_analysis(
    partner_profiles: Dict[str, Dict[str, Any]],
    locations: List[str],
    commute_band_km: Tuple[int, int],
    distance_unit: str,
    relocation_willing: bool,
    travel_tolerance: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not locations:
        return results

    for location in locations:
        p1_signal = _market_signal(partner_profiles["partner1"], location)
        p2_signal = _market_signal(partner_profiles["partner2"], location)
        if not p1_signal["job_estimate"] and not p2_signal["job_estimate"]:
            continue

        commute_km = _estimate_commute(commute_band_km, p1_signal, p2_signal)
        commute_display = int(round(_convert_distance_from_km(commute_km, distance_unit)))

        combined_midpoint = (
            (partner_profiles["partner1"]["salary_range"][0] + partner_profiles["partner1"]["salary_range"][1]) // 2
            + (partner_profiles["partner2"]["salary_range"][0] + partner_profiles["partner2"]["salary_range"][1]) // 2
        )

        travel_bonus = 5 if "High" in travel_tolerance else 0
        relocation_bonus = 5 if relocation_willing else 0
        score = min(
            100,
            55
            + min(p1_signal["job_estimate"], 220) * 0.12
            + min(p2_signal["job_estimate"], 220) * 0.12
            + travel_bonus
            + relocation_bonus
            - (commute_km / 10),
        )

        exa_insight = _fetch_exa_insight(location, p1_signal["role_hint"] or p2_signal["role_hint"])

        results.append({
            "city": location,
            "score": round(score, 1),
            "p1_jobs": p1_signal["job_estimate"],
            "p2_jobs": p2_signal["job_estimate"],
            "avg_commute": commute_display,
            "avg_commute_unit": distance_unit,
            "combined_salary": _format_currency(combined_midpoint),
            "travel_tolerance": travel_tolerance,
            "exa_insight": exa_insight,
        })

    return sorted(results, key=lambda item: item["score"], reverse=True)


def _process_resume_upload(uploaded_file, partner_key: str, partner_label: str) -> None:
    """Route uploaded resume through Complete Data Parser via ResumeService."""
    if not uploaded_file or not RESUME_SERVICE:
        return

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    hash_key = f"{partner_key}_upload_hash"
    if st.session_state.get(hash_key) == file_hash:
        return

    with NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        parsed = RESUME_SERVICE.parse(temp_path, user_id=st.session_state.get("user_id"))
        if parsed.get("error"):
            st.error(f"{partner_label}: resume parsing failed — {parsed['error']}")
            return

        if INTELLIGENCE_SERVICE:
            try:
                parsed = INTELLIGENCE_SERVICE.enrich(parsed, user_id=st.session_state.get("user_id"))
            except Exception as exc:  # pragma: no cover - diagnostic path
                st.warning(f"{partner_label}: enrichment fallback engaged ({exc})")

        st.session_state[f"{partner_key}_parsed_resume"] = parsed
        st.session_state[hash_key] = file_hash
        st.success(
            f"{partner_label}: Resume parsed via admin Complete Data Parser and synced to Dual Career Suite"
        )
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


def _render_partner_resume_summary(partner_key: str, partner_label: str) -> None:
    parsed = st.session_state.get(f"{partner_key}_parsed_resume")
    if not parsed:
        return

    skills = _extract_skills(parsed)
    summary = parsed.get("summary") or parsed.get("content", "")[:400]
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(f"{partner_label} skill signals", len(skills))
    with col_b:
        st.metric(f"{partner_label} ATS keywords", parsed.get("real_ai_analysis", {}).get("pattern_count", len(skills)))
    with col_c:
        st.metric(f"{partner_label} ingestion status", "Synced" if parsed.get("ai_ingestion") else "Pending")

    with st.expander(f"View parsed insights for {partner_label}", expanded=False):
        if summary:
            st.write(summary)
        if skills:
            st.write(
                "Top skills:",
                ", ".join(skills[:15]) + (" …" if len(skills) > 15 else ""),
            )
        if parsed.get("ai_ingestion"):
            st.json(parsed["ai_ingestion"])

st.set_page_config(
    page_title="Dual Career Suite - IntelliCV",
    page_icon="💑",
    layout="wide"
)

# Check authentication
if not st.session_state.get("authenticated_user"):
    st.warning("🔐 Please login to access the Dual Career Suite")
    st.stop()

# Check subscription tier
tier = st.session_state.get("subscription_tier", "free")
if tier not in ["annual_pro", "enterprise_pro"]:
    st.warning("🔒 Dual Career Suite requires Annual Pro or Enterprise Pro subscription")
    st.info("**Upgrade to unlock:** Dual job search optimization, geographic feasibility, partner profile integration")
    if st.button("⬆️ Upgrade to Annual Pro"):
        st.switch_page("pages/06_Pricing.py")
    st.stop()

# Main content
st.title("💑 Dual Career Suite")
st.markdown("### Optimize Career Opportunities for You and Your Partner")

st.info("""
🎯 **Partner Optimization Features:**
- Upload both partner resumes and career profiles
- Search for job opportunities optimized for BOTH careers
- Geographic feasibility analysis (travel distances, relocation options)
- Comparative analysis: Which location offers best opportunities for both?
- Dual salary optimization
- Work-life balance metrics
""")

if RESUME_SERVICE is None:
    st.error("Admin Complete Data Parser is unavailable. Open the admin portal and load the Complete Data Parser page to enable resume syncing.")
elif RESUME_SERVICE_ERROR:
    st.warning(f"Complete Data Parser warning: {RESUME_SERVICE_ERROR}")

if EXA_ERROR and not EXA_AVAILABLE:
    st.warning("EXA insights are disabled — add a valid EXA API key in .env to unlock deep web signals.")

# Partner profile section
st.markdown("---")
st.markdown("### 👥 Partner Profiles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 👤 Partner 1 (You)")

    partner1_name = st.text_input(
        "Name",
        value=st.session_state.get("user_id", ""),
        key="partner1_name"
    )

    partner1_resume = st.file_uploader(
        "Upload Resume (PDF, DOCX)",
        type=["pdf", "docx"],
        key="partner1_resume"
    )

    partner1_career = st.text_area(
        "Career Goals",
        value=st.session_state.get("partner1_career", ""),
        key="partner1_career"
    )

    partner1_location_pref = st.text_input(
        "Preferred Locations (comma-separated)",
        value=st.session_state.get("partner1_loc", ""),
        key="partner1_loc"
    )

    partner1_salary_range = st.slider(
        "Target Salary Range ($0 – $1M)",
        min_value=0,
        max_value=1_000_000,
        value=st.session_state.get("partner1_salary_range_value", (0, 200000)),
        step=5000,
    )
    st.session_state["partner1_salary_range_value"] = partner1_salary_range

_process_resume_upload(partner1_resume, "partner1", "Partner 1")

with col2:
    st.markdown("#### 👤 Partner 2")

    st.warning("⚠️ **ONE-TIME SETUP**: Partner profile can only be set once. Contact support to modify.")

    partner2_name = st.text_input(
        "Partner Name",
        key="partner2_name"
    )

    partner2_resume = st.file_uploader(
        "Upload Partner Resume (PDF, DOCX)",
        type=["pdf", "docx"],
        key="partner2_resume"
    )

    partner2_career = st.text_area(
        "Partner Career Goals",
        value=st.session_state.get("partner2_career", ""),
        key="partner2_career"
    )

    partner2_location_pref = st.text_input(
        "Partner Preferred Locations (comma-separated)",
        value=st.session_state.get("partner2_loc", ""),
        key="partner2_loc"
    )

    partner2_salary_range = st.slider(
        "Partner Salary Range ($0 – $1M)",
        min_value=0,
        max_value=1_000_000,
        value=st.session_state.get("partner2_salary_range_value", (0, 180000)),
        step=5000,
    )
    st.session_state["partner2_salary_range_value"] = partner2_salary_range

_process_resume_upload(partner2_resume, "partner2", "Partner 2")

_render_partner_resume_summary("partner1", "Partner 1")
_render_partner_resume_summary("partner2", "Partner 2")

# Search constraints
st.markdown("---")
st.markdown("### 🎯 Dual Search Constraints")

col_distance, col_relocation = st.columns([2, 1])

with col_distance:
    distance_unit = st.selectbox(
        "Distance Unit",
        ["Kilometers", "Miles"],
        key="dual_distance_unit"
    )

with col_relocation:
    relocation_willing = st.checkbox("Willing to relocate?", value=True)

unit_label = "km" if distance_unit == "Kilometers" else "mi"
commute_display_default = st.session_state.get("dual_commute_window", (0, 120))
commute_display = st.slider(
    f"Preferred Commute Window (0 – 500 {unit_label})",
    min_value=0,
    max_value=500,
    value=commute_display_default,
    step=5,
)
st.session_state["dual_commute_window"] = commute_display

if distance_unit == "Miles":
    commute_band_km: Tuple[int, int] = (
        int(_convert_distance_to_km(commute_display[0], distance_unit)),
        int(_convert_distance_to_km(commute_display[1], distance_unit))
    )
else:
    commute_band_km = commute_display

travel_tolerance = st.selectbox(
    "Travel Distance Tolerance",
    [
        f"Low (both same city / ≤25 {unit_label})",
        f"Medium (within 50 {unit_label})",
        f"High (within 100 {unit_label})",
        "Very High (different states OK)",
    ]
)

# Action button
st.markdown("---")
find_button = st.button("🔍 Find Dual Career Opportunities", type="primary", use_container_width=True)

if find_button:
    partner_profiles = {
        "partner1": _get_partner_profile(
            name=partner1_name,
            career_goals=partner1_career,
            location_text=partner1_location_pref,
            salary_range=tuple(st.session_state.get("partner1_salary_range_value", (0, 0))),
            parsed_resume=st.session_state.get("partner1_parsed_resume"),
        ),
        "partner2": _get_partner_profile(
            name=partner2_name,
            career_goals=partner2_career,
            location_text=partner2_location_pref,
            salary_range=tuple(st.session_state.get("partner2_salary_range_value", (0, 0))),
            parsed_resume=st.session_state.get("partner2_parsed_resume"),
        ),
    }

    location_candidates: List[str] = []
    for partner_key in ("partner1", "partner2"):
        for city in partner_profiles[partner_key]["locations"]:
            if city not in location_candidates:
                location_candidates.append(city)

    if not location_candidates:
        st.error("Add at least one preferred location for either partner to run the dual search.")
    else:
        with st.spinner("🔄 Running Complete Data Parser + EXA insights..."):
            analysis_results = _run_dual_analysis(
                partner_profiles,
                location_candidates,
                commute_band_km=commute_band_km,
                distance_unit=distance_unit,
                relocation_willing=relocation_willing,
                travel_tolerance=travel_tolerance,
            )

        if not analysis_results:
            st.warning(
                "No opportunities surfaced yet. Confirm that resumes parsed successfully in the admin Complete Data Parser."
            )
        else:
            st.success("✅ Dual career analysis complete!")
            st.markdown("### 📊 Dual Career Analysis Results")
            st.markdown("#### 🎯 Optimized Locations (Live data)")

            for idx, result in enumerate(analysis_results, 1):
                with st.expander(f"#{idx} · {result['city']} (Score {result['score']}/100)"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Partner 1 Opportunities", result["p1_jobs"])
                    with col2:
                        st.metric("Partner 2 Opportunities", result["p2_jobs"])
                    with col3:
                        st.metric(
                            "Avg Commute",
                            f"{result['avg_commute']} {result['avg_commute_unit']}"
                        )
                    with col4:
                        st.metric("Combined Salary Target", result["combined_salary"])

                    st.info(
                        f"📍 **Signal:** {result['city']} balances {travel_tolerance.lower()} with "
                        f"Complete Data Parser skill matches."
                    )

                    if result.get("exa_insight"):
                        exa_info = result["exa_insight"]
                        st.caption(
                            f"EXA snapshot: [{exa_info.get('title','source')}]({exa_info.get('url','')})"
                        )

# Partner pricing info
st.markdown("---")
st.markdown("### 💰 Partner Subscription Pricing")

st.info("""
**Dual Career Suite Pricing:**
- +1 Partner: Additional 50% of your subscription fee
- Elite Concierge Add-on: Additional 50% for EXA + geolocation concierge mirroring admin portal
- +2 Partners: Additional 25% each (for polyamorous relationships)

**Example:** Annual Pro ($149.99/year)
- +1 Partner: $149.99 + $74.99 = $224.98/year
- +1 Partner + Elite Concierge: $149.99 + $74.99 + $74.99 = $299.97/year
- +2 Partners: $149.99 + $37.50 + $37.50 = $224.99/year
""")

# Future features
st.markdown("---")
st.markdown("### 🚀 Coming Soon")

st.warning("""
**Future Enhancements (Q1 2026):**
- 🗺️ Interactive map visualization showing optimal job clusters
- 🎯 Dartboard view showing "bulls-eye" proximity to perfect match
- 📈 Historical tracking of dual search progress
- 🤝 Couple's interview coordination calendar
- 💬 Partner communication templates for discussing opportunities
""")
