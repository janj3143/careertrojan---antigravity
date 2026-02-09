"""
🏪 Mentorship Marketplace - Directory of Sector-Specific Mentorship Offers
===========================================================================
Browse mentorship programs organized by industry sectors and specializations.

NOTES:
- Directory of MENTORSHIP OFFERS (by sector), NOT individual people
- Search by sector/specialization to find structured mentorship programs
- Requires Annual Pro subscription (£299/year) for full access
- Programs include: session packages, learning paths, and expert guidance

Token Cost: 30 tokens (Annual Pro or Enterprise required)
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# -------------------------------------------------------------------
# CONFIG: API wiring (no demo data)
# -------------------------------------------------------------------
MENTORSHIP_API_BASE = (
    st.secrets.get("MENTORSHIP_API_BASE", "")
    or os.environ.get("MENTORSHIP_API_BASE", "")
).rstrip("/")


def _api_available() -> bool:
    return bool(MENTORSHIP_API_BASE)


def _safe_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Thin HTTP helper. Returns {} on failure. No mock/demo payloads.
    Expected JSON envelope from backend:
      { "data": [...], "meta": {...} }
    """
    if not _api_available():
        return {}
    url = f"{MENTORSHIP_API_BASE}{path}"
    try:
        resp = requests.get(url, params=params or {}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        # No silent fake data – caller handles empty dict
        return {}


# -------------------------------------------------------------------
# SERVICE-LIKE HELPERS (all return live data or empty)
# -------------------------------------------------------------------
def search_mentorship_offers(
    sector: str,
    specializations: List[str],
    program_type: str,
    price_range: str,
    delivery_mode: Optional[List[str]] = None,
    time_commitment: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query backend for available mentorship offers.
    Returns [] if no API / no data; never returns demo content.
    """
    payload = {
        "sector": sector,
        "specializations": specializations,
        "program_type": program_type,
        "price_range": price_range,
        "delivery_mode": delivery_mode or [],
        "time_commitment": time_commitment,
    }
    res = _safe_get("/mentorship/offers/search", params={"q": st.session_state.get("user_id", ""), **payload})
    offers = res.get("data") or []
    return offers if isinstance(offers, list) else []


def list_featured_offers() -> List[Dict[str, Any]]:
    """
    Featured programs – pulled from backend.
    """
    res = _safe_get("/mentorship/offers/featured")
    offers = res.get("data") or []
    return offers if isinstance(offers, list) else []


def list_programs_by_format(
    program_format: str,
    delivery_mode: List[str],
    time_commitment: str,
) -> List[Dict[str, Any]]:
    """
    Programs filtered by structure/duration.
    """
    res = _safe_get(
        "/mentorship/programs/by-format",
        params={
            "format": program_format,
            "delivery_mode": ",".join(delivery_mode),
            "time_commitment": time_commitment,
        },
    )
    programs = res.get("data") or []
    return programs if isinstance(programs, list) else []


def get_user_active_programs(user_id: str) -> List[Dict[str, Any]]:
    """
    Active mentorship programs for current user.
    """
    res = _safe_get(f"/mentorship/users/{user_id}/programs/active")
    programs = res.get("data") or []
    return programs if isinstance(programs, list) else []


def get_user_mentorship_metrics(user_id: str) -> Dict[str, Any]:
    """
    Aggregated metrics for the user journey.
    Expected keys (all optional): total_programs, sessions_completed,
    avg_rating, goals, resources, etc.
    """
    res = _safe_get(f"/mentorship/users/{user_id}/metrics")
    metrics = res.get("data") or {}
    return metrics if isinstance(metrics, dict) else {}


def list_success_stories() -> List[Dict[str, Any]]:
    """
    Pull real success stories from backend.
    """
    res = _safe_get("/mentorship/success-stories")
    stories = res.get("data") or []
    return stories if isinstance(stories, list) else []


def get_impact_metrics() -> pd.DataFrame:
    """
    Impact metrics, if backend provides them.
    Expected format:
      { "data": [ { "metric": "...", "avg": 0-100, "top10": 0-100 }, ... ] }
    """
    res = _safe_get("/mentorship/impact-metrics")
    rows = res.get("data") or []
    if not isinstance(rows, list) or not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Normalize common keys if needed
    if {"Metric", "Average Improvement", "Top 10% Improvement"}.issubset(df.columns):
        return df
    # Fallback column mapping
    cols_map = {
        "metric": "Metric",
        "avg": "Average Improvement",
        "average_improvement": "Average Improvement",
        "top10": "Top 10% Improvement",
        "top_10_improvement": "Top 10% Improvement",
    }
    df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})
    return df


def get_recent_testimonials() -> List[str]:
    """
    Short testimonial strings for the UI.
    """
    res = _safe_get("/mentorship/testimonials/recent")
    testimonials = res.get("data") or []
    # Allow either list[str] or list[dict] with "quote"/"text"
    if testimonials and isinstance(testimonials[0], dict):
        return [
            t.get("text")
            or t.get("quote")
            or ""
            for t in testimonials
        ]
    return [t for t in testimonials if isinstance(t, str)]


# -------------------------------------------------------------------
# PAGE CONFIG & ACCESS CONTROL
# -------------------------------------------------------------------
st.set_page_config(
    page_title="🏪 Mentorship Marketplace - IntelliCV",
    page_icon="🏪",
    layout="wide",
)

# Authentication check
if not st.session_state.get("authenticated_user"):
    st.error("🔒 Please log in to access Mentorship Marketplace")
    if st.button("🏠 Return to Home"):
        st.switch_page("main.py")
    st.stop()

# Tier check - requires Annual Pro or Enterprise
user_tier = st.session_state.get("subscription_tier", "free")
if user_tier not in ["annual_pro", "enterprise_pro"]:
    st.warning("⭐ **Mentorship Marketplace requires Annual Pro subscription (£299/year)**")

    st.markdown(
        """
        ### 🏪 What You'll Get Access To

        - 📁 **Sector-Specific Mentorship Programs**: Organized by industry and specialization
        - 🎯 **Structured Learning Paths**: Multi-session programs with clear outcomes
        - 🏅 **Expert Guidance**: Industry veterans and curated programs
        - 📊 **Progress Tracking**: Measure your growth through mentorship
        - 🌟 **Premium Support**: Priority matching and scheduling

        This is a directory of **mentorship offers** (organized by sector), not individual people.
        """
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "⬆️ Upgrade to Annual Pro (£299/year)",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("pages/06_Pricing.py")
    st.stop()


def render_api_status_banner() -> None:
    """
    Light banner if the mentorship API endpoint is not yet wired.
    This is NOT demo data – just a wiring hint.
    """
    if not _api_available():
        st.info(
            "⚙️ Mentorship API endpoint is not configured yet. "
            "Set `MENTORSHIP_API_BASE` in environment or Streamlit secrets "
            "to enable live marketplace data."
        )


def main() -> None:
    st.title("🏪 Mentorship Marketplace")
    st.markdown("### Directory of Sector-Specific Mentorship Programs & Offers")
    st.info(
        "💡 **Browse mentorship offers organized by sector** – structured programs, not individual profiles."
    )

    # Token cost display
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("💎 **Token Cost: 30 tokens** | Annual Pro Feature ✅")

    render_api_status_banner()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🏪 Browse by Sector",
            "🎯 Mentorship Programs",
            "📊 My Mentorships",
            "🌟 Success Stories",
        ]
    )

    # ------------------------------------------------------------------
    # TAB 1: Browse by Sector
    # ------------------------------------------------------------------
    with tab1:
        st.header("🏪 Browse Mentorship Offers by Sector")
        st.markdown(
            "**Find structured mentorship programs in your industry or target specialization**"
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("🔍 Search by Sector")

            sector_category = st.selectbox(
                "Industry Sector",
                [
                    "Technology & Engineering",
                    "Data Science & AI/ML",
                    "Product & Design",
                    "Business & Strategy",
                    "Leadership & Management",
                    "Entrepreneurship & Startups",
                    "Finance & Investment",
                    "Marketing & Sales",
                ],
            )

            specialization = st.multiselect(
                "Specializations",
                [
                    "Machine Learning Engineering",
                    "Data Science",
                    "Software Architecture",
                    "Engineering Leadership",
                    "Product Management",
                    "Career Transition",
                    "Executive Coaching",
                    "Startup Founding",
                ],
                default=["Machine Learning Engineering"],
            )

            program_type = st.selectbox(
                "Program Type",
                [
                    "All Types",
                    "Short-term (4-6 sessions)",
                    "Standard (8-12 sessions)",
                    "Long-term (6+ months)",
                    "Project-based",
                    "Career Transition",
                ],
            )

            price_range = st.select_slider(
                "Price Range (Total Program)",
                options=[
                    "Under £200",
                    "£200-£500",
                    "£500-£1000",
                    "£1000-£2000",
                    "£2000+",
                ],
                value="£500-£1000",
            )

            search_clicked = st.button(
                "🔍 Search Mentorship Offers", type="primary"
            )

        with col2:
            st.subheader("⭐ Featured Mentorship Programs")
            st.markdown("*Structured programs organized by sector and outcomes*")

            featured_offers: List[Dict[str, Any]] = list_featured_offers()

            if search_clicked:
                with st.spinner("Searching mentorship offers..."):
                    offers = search_mentorship_offers(
                        sector=sector_category,
                        specializations=specialization,
                        program_type=program_type,
                        price_range=price_range,
                    )
                count = len(offers)
                if count:
                    st.success(f"✅ Found {count} mentorship program(s) matching your criteria.")
                    featured_offers = offers  # Show search result as main list
                else:
                    st.warning(
                        "No mentorship offers match these filters yet. Try adjusting your search."
                    )

            if not featured_offers:
                st.info(
                    "No mentorship programs are published yet. "
                    "Once the admin portal publishes sector programs, they will appear here."
                )
            else:
                for offer in featured_offers:
                    program_name = offer.get("program_name") or offer.get("name") or "Mentorship Program"
                    sector = offer.get("sector") or offer.get("industry") or "Sector not specified"
                    focus = offer.get("focus") or offer.get("summary") or "Focus not specified"
                    sessions = offer.get("sessions") or offer.get("duration") or ""
                    format_label = offer.get("format") or offer.get("delivery_mode") or ""
                    outcomes = offer.get("outcomes") or []
                    price = offer.get("price") or offer.get("investment") or "Price on request"
                    rating = offer.get("rating")
                    participants = offer.get("participants") or offer.get("enrolments")

                    with st.expander(f"🎯 **{program_name}** ({sector})", expanded=True):
                        col_a, col_b = st.columns([2, 1])

                        with col_a:
                            st.markdown(f"**Focus**: {focus}")
                            if sessions or format_label:
                                st.markdown(
                                    f"**Format**: {sessions} {'• ' if sessions and format_label else ''}{format_label}"
                                )

                            if outcomes:
                                st.markdown("**Program Outcomes:**")
                                for outcome in outcomes:
                                    st.markdown(f"  ✅ {outcome}")

                        with col_b:
                            st.metric("Investment", str(price))
                            if rating is not None:
                                st.metric("Rating", f"{float(rating):.1f}/5.0")
                            if participants:
                                st.markdown(f"*{participants} participant(s)*")

                            if st.button(
                                "📋 View Full Details",
                                key=f"details_{program_name}_{sector}",
                                use_container_width=True,
                            ):
                                st.info(
                                    "Full program details panel will open here once wired to the detail endpoint."
                                )

                            if st.button(
                                "🎯 Express Interest",
                                key=f"interest_{program_name}_{sector}",
                                use_container_width=True,
                                type="primary",
                            ):
                                # We only log a local event; no fake server calls.
                                st.success(
                                    "✅ Interest registered. Once the live backend is connected, "
                                    "your request will be submitted to the mentorship team."
                                )

    # ------------------------------------------------------------------
    # TAB 2: Programs by Format & Duration
    # ------------------------------------------------------------------
    with tab2:
        st.header("🎯 Mentorship Programs by Format & Duration")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("📋 Filter by Format")

            program_format = st.radio(
                "Program Structure",
                [
                    "Short-term Intensive (4-6 sessions)",
                    "Standard Program (8-12 sessions)",
                    "Long-term Mentorship (6+ months)",
                    "Project-based Coaching",
                    "Career Transition Programs",
                ],
            )

            delivery_mode = st.multiselect(
                "Delivery Mode",
                [
                    "1-on-1 Video Sessions",
                    "Group Cohorts",
                    "Hybrid (Individual + Group)",
                    "Async + Sync Mix",
                    "Workshop Series",
                ],
                default=["1-on-1 Video Sessions"],
            )

            time_commitment = st.select_slider(
                "Weekly Time Commitment",
                options=["1-2 hours", "2-4 hours", "4-6 hours", "6-8 hours", "8+ hours"],
                value="2-4 hours",
            )

            st.subheader("🎯 Program Outcomes")
            st.markdown(
                """
                Select your primary goal (used by the backend to rank offers):

                - 🚀 **Promotion/Advancement**
                - 💡 **Skill Development**
                - 🔄 **Career Transition**
                - 👥 **Leadership Growth**
                - 🏢 **Entrepreneurship**
                """
            )

        with col2:
            st.subheader("📦 Program Offerings")

            with st.spinner("Loading programs for selected format..."):
                programs = list_programs_by_format(
                    program_format=program_format,
                    delivery_mode=delivery_mode,
                    time_commitment=time_commitment,
                )

            if not programs:
                st.info(
                    "No mentorship programs are currently published for this format. "
                    "Once the admin marketplace is populated, matching programs will appear here."
                )
            else:
                for program in programs:
                    name = program.get("name") or "Mentorship Program"
                    sector = program.get("sector") or program.get("industry") or "Sector not specified"
                    duration = program.get("duration") or program.get("sessions") or ""
                    fmt = program.get("format") or program.get("delivery_mode") or ""
                    outcomes = program.get("outcomes") or []
                    price = program.get("price") or program.get("investment") or "Price on request"

                    with st.expander(f"📘 **{name}**", expanded=True):
                        col_p1, col_p2 = st.columns([2, 1])

                        with col_p1:
                            st.markdown(f"**Sector**: {sector}")
                            if duration:
                                st.markdown(f"**Duration**: {duration}")
                            if fmt:
                                st.markdown(f"**Format**: {fmt}")

                            if outcomes:
                                st.markdown("**Expected Outcomes:**")
                                for outcome in outcomes:
                                    st.markdown(f"  ✅ {outcome}")

                        with col_p2:
                            st.metric("Investment", str(price))
                            st.markdown("---")
                            if st.button(
                                "📋 Full Details",
                                key=f"details2_{name}",
                                use_container_width=True,
                            ):
                                st.info("Full program details will load here from the live backend.")
                            if st.button(
                                "🎯 Apply Now",
                                key=f"apply_{name}",
                                use_container_width=True,
                                type="primary",
                            ):
                                st.success(
                                    "✅ Application request captured locally. "
                                    "Wire this button to your backend to submit real applications."
                                )

    # ------------------------------------------------------------------
    # TAB 3: My Mentorships
    # ------------------------------------------------------------------
    with tab3:
        st.header("📊 My Mentorships")

        user_id = str(st.session_state.get("user_id", "")) or "anonymous"

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Active Programs")

            active_programs = get_user_active_programs(user_id=user_id)

            if not active_programs:
                st.info(
                    "You don't have any active mentorship programs recorded yet. "
                    "Once you join a program, it will appear here with progress tracking."
                )
            else:
                for prog in active_programs:
                    prog_name = prog.get("program") or prog.get("name") or "Mentorship Program"
                    sector = prog.get("sector") or prog.get("industry") or "Sector not specified"
                    sessions_completed = prog.get("sessions_completed", 0)
                    sessions_total = prog.get("sessions_total", 0)
                    progress = prog.get("progress") or (
                        (sessions_completed / sessions_total * 100)
                        if sessions_total
                        else 0
                    )
                    next_session = prog.get("next_session") or ""
                    mentor_assigned = prog.get("mentor_assigned")

                    with st.expander(f"📘 {prog_name}", expanded=True):
                        st.markdown(f"**Sector**: {sector}")
                        if sessions_total:
                            st.markdown(
                                f"**Progress**: {sessions_completed}/{sessions_total} sessions"
                            )
                        st.progress(max(0, min(1, float(progress) / 100)))
                        if next_session:
                            st.markdown(f"**Next Session**: {next_session}")
                        if mentor_assigned is not None:
                            st.markdown(
                                f"**Mentor Assigned**: {'Yes' if mentor_assigned else 'Pending'}"
                            )

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(
                                "📅 Reschedule",
                                key=f"resched_{prog_name[:10]}",
                            ):
                                st.info(
                                    "Reschedule workflow will be wired here once calendar integration is available."
                                )
                        with col_b:
                            if st.button(
                                "📝 Session Notes",
                                key=f"notes_{prog_name[:10]}",
                            ):
                                st.info(
                                    "Session notes viewer/editor will appear here using live session data."
                                )

        with col2:
            st.subheader("📈 Your Mentorship Journey")

            metrics = get_user_mentorship_metrics(user_id=user_id)
            total_programs = metrics.get("total_programs")
            sessions_completed = metrics.get("sessions_completed")
            avg_rating = metrics.get("avg_rating")

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric(
                    "Total Programs",
                    str(total_programs) if total_programs is not None else "—",
                )
            with col_m2:
                st.metric(
                    "Sessions Completed",
                    str(sessions_completed) if sessions_completed is not None else "—",
                )
            with col_m3:
                st.metric(
                    "Avg Rating Given",
                    f"{float(avg_rating):.1f}/5" if avg_rating is not None else "—",
                )

            st.subheader("🎯 Goals Progress")

            goals = metrics.get("goals") or []
            if not goals:
                st.info(
                    "No mentorship goals are recorded yet. "
                    "Once your mentor or the admin portal adds structured goals, "
                    "they will appear here with progress bars."
                )
            else:
                for goal in goals:
                    label = goal.get("label") or goal.get("goal") or "Goal"
                    target_date = goal.get("target_date") or ""
                    progress = goal.get("progress") or 0
                    st.markdown(f"**{label}**" + (f" (Target: {target_date})" if target_date else ""))
                    st.progress(max(0, min(1, float(progress) / 100)))
                    st.markdown(f"{progress:.0f}% complete")
                    st.markdown("---")

            st.subheader("📚 Learning Resources")
            resources = metrics.get("resources") or {}
            if not resources:
                st.info(
                    "When your mentorship programs publish curated resources (reading, videos, certifications), "
                    "they'll be summarised here."
                )
            else:
                # Expected structure: {'articles': n, 'videos': n, 'certifications': n, 'network_intros': n}
                st.markdown(
                    f"""
                    - 📖 Recommended Reading: {resources.get('articles', '—')}
                    - 🎥 Video Courses: {resources.get('videos', '—')}
                    - 🏆 Certifications: {resources.get('certifications', '—')}
                    - 🔗 Network Connections: {resources.get('network_intros', '—')}
                    """
                )

    # ------------------------------------------------------------------
    # TAB 4: Success Stories & Impact
    # ------------------------------------------------------------------
    with tab4:
        st.header("🌟 Success Stories")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏆 Featured Success Stories")

            stories = list_success_stories()
            if not stories:
                st.info(
                    "Success stories will appear here once mentees opt-in to share outcomes "
                    "through the admin portal."
                )
            else:
                for story in stories:
                    mentee = story.get("mentee") or story.get("name") or "Mentee"
                    before = story.get("before") or "Previous role"
                    after = story.get("after") or "New role"
                    timeline = story.get("timeline") or ""
                    mentor = story.get("mentor") or ""
                    outcome = story.get("outcome") or ""
                    narrative = story.get("story") or story.get("narrative") or ""
                    testimonial = story.get("testimonial") or ""

                    title = f"{mentee}: {before} → {after}"
                    with st.expander(f"🎯 {title}"):
                        if timeline:
                            st.write(f"**Timeline:** {timeline}")
                        if mentor:
                            st.write(f"**Mentor / Program:** {mentor}")
                        if outcome:
                            st.write(f"**Outcome:** {outcome}")
                        if narrative:
                            st.write(f"**Story:** {narrative}")
                        if testimonial:
                            st.success(f"💬 **Testimonial:** \"{testimonial}\"")

        with col2:
            st.subheader("📊 Impact Metrics")

            impact_df = get_impact_metrics()
            if impact_df.empty:
                st.info(
                    "Impact metrics will be displayed here once the mentorship analytics "
                    "service is wired and has sufficient anonymised data."
                )
            else:
                value_cols = [
                    col
                    for col in impact_df.columns
                    if col.lower() not in {"metric", "measure"}
                ]
                if value_cols:
                    fig = px.bar(
                        impact_df,
                        x="Metric",
                        y=value_cols,
                        title="Career Impact Metrics (%)",
                        barmode="group",
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

            st.subheader("💬 Recent Testimonials")

            testimonials = get_recent_testimonials()
            if not testimonials:
                st.info(
                    "Recent testimonials will appear here once users submit feedback "
                    "through the live mentorship feedback flow."
                )
            else:
                for t in testimonials:
                    if t:
                        st.write(t)

            if st.button("📝 Share Your Success Story"):
                st.success(
                    "✅ Success story submission flow will open here once wired to the backend."
                )


if __name__ == "__main__":
    main()


Look at this modification code and integrate it - and remove reduntant code
