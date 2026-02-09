"""
Page 10 – UMarketU Suite

"You marketing you" – end-to-end journey:
1. Use your **parsed resume** as the anchor.
2. Discover real roles and job descriptions from your **job index / backend**.
3. Analyse **fit & overlap** (skills, keywords, strengths, gaps).
4. Generate **tuned, job-aware resume variants** (JSON – ready for export).
5. Track job applications and status in one place.
6. Optionally bring in a **partner resume** for dual-career planning.

IMPORTANT DESIGN DECISION
-------------------------
Historically, a lot of this logic lived directly in this page:
- manual keyword extraction & overlap
- inline STAR & interview prep
- job search heuristics
- direct parsing of uploads

In the current architecture we have moved most of the *heavy intelligence* to:

- services.resume_service.ResumeService
    - Parses resumes
    - Manages active/master resume
    - Handles promotion of tuned versions
- services.ai_service.AIScoringService
    - Scores resume vs job
    - Generates tuned resumes
- services.user_data_service.UserDataService
    st.caption(
        "This is deliberately high-level. Detailed partner-aware coaching can live "
        "in future Coaching / Mentorship modules once the data is available."
    )
    USER_DATA_SERVICE_AVAILABLE = True
except Exception:
    user_data_service = None
    USER_DATA_SERVICE_AVAILABLE = False

# Token management (for visibility on LLM usage)
try:
    from token_management_system import init_token_system_for_page

    token_manager = init_token_system_for_page()
    TOKEN_MANAGER_AVAILABLE = True
except Exception:  # pragma: no cover
    token_manager = None
    TOKEN_MANAGER_AVAILABLE = False

# AI scoring & tuning (resume vs JD)
try:
    from services.ai_service import AIScoringService

    ai_service = AIScoringService()
    AI_SERVICE_AVAILABLE = True
except Exception:
    ai_service = None
    AI_SERVICE_AVAILABLE = False

# Resume parsing & master resume
try:
    from services.resume_service import ResumeService

    resume_service = ResumeService()
    RESUME_SERVICE_AVAILABLE = True
except Exception:
    resume_service = None
    RESUME_SERVICE_AVAILABLE = False


# ============================================================================
#  SESSION HELPERS
# ============================================================================

STATE_KEY = "umarketu_state"


def _get_state() -> Dict[str, Any]:
    """
    Local page session state for UMarketU.

    Mirrors the legacy design:
    - selected_job: the job currently in focus
    - fit_analysis: overlap / gaps for selected_job
    - tuned_resume: job-specific tuned resume JSON
    - applications: user's application tracker entries
    - partner: partner resume snapshot
    """
    return st.session_state.setdefault(
        STATE_KEY,
        {
            "selected_job": None,
            "fit_analysis": None,
            "tuned_resume": None,
            "applications": [],
            "partner": {"snapshot": None, "resume_json": None},
            "selected_application_for_coach": None,
        },
    )


def _set_state(state: Dict[str, Any]) -> None:
    st.session_state[STATE_KEY] = state


def _get_user_silo(user) -> Dict[str, Path]:
    """
    Returns per-user file system silo, so we can read/write:
    - ai_json
    - application tracker
    - partner resume JSON
    """
    try:
        return get_user_silo_paths(user)
    except Exception:
        return {"root": USER_PORTAL_DATA_DIR}


# ============================================================================
#  DATA LOADING – RESUME & JOB INDEX
# ============================================================================

def load_master_resume_snapshot(user) -> Optional[Dict[str, Any]]:
    """
    Get the active/master resume snapshot for this user.

    Priority:
    0. Fresh hybrid snapshot from Resume Upload page (session_state)
    1. Backend resume service (canonical active version)
    2. working_copy / ai_json JSON fallback
    """
    # 0) If we just enriched a resume on the upload page, use that first
    hybrid_snapshot = st.session_state.get("hybrid_resume_snapshot")
    if isinstance(hybrid_snapshot, dict):
        return hybrid_snapshot

    # 1) Backend service
    if RESUME_SERVICE_AVAILABLE:
        try:
            return resume_service.get_active_resume_snapshot(user.id)
        except Exception:
            pass

    # 2) Fallback: load from user_silo JSON
    silo = _get_user_silo(user)
    json_dir = silo.get("json") or (silo["root"] / "working_copy" / "ai_json")
    if not json_dir.exists():
        return None

    latest = sorted(json_dir.glob("*.json"))[-1:]
    if not latest:
        return None

    try:
        return json.loads(latest[0].read_text(encoding="utf-8"))
    except Exception:
        return None


    # Fallback: latest JSON in user silo
    silo = _get_user_silo(user)
    json_dir = silo.get("json") or (silo["root"] / "working_copy" / "ai_json")
    if not json_dir.exists():
        return None

    latest_files = sorted(json_dir.glob("*.json"))
    if not latest_files:
        return None

    try:
        return json.loads(latest_files[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_resume_keywords(snapshot: Dict[str, Any]) -> List[str]:
    """
    Extracts the keyword universe from the resume snapshot.

    - Explicit skill lists: snapshot["skills"]
    - AI-derived lists: snapshot["ai_keywords"], snapshot["inferred_keywords"]

    This mirrors your original design where we treat skills + AI-suggested
    keywords as one blended feature set.
    """
    skills = snapshot.get("skills", []) or []
    kw = {s.strip() for s in skills if isinstance(s, str) and s.strip()}

    for bucket in ("ai_keywords", "inferred_keywords"):
        for val in snapshot.get(bucket, []) or []:
            if isinstance(val, str) and val.strip():
                kw.add(val.strip())

    return sorted(kw)

def get_resume_snapshot(user) -> Optional[Dict[str, Any]]:
    """
    Get the resume snapshot for coaching flows.

    Priority:
    0. hybrid_resume_snapshot from Resume Upload page (8-model hybrid)
    1. resume_data stored locally in session
    2. Future: backend active resume service (if we wire it in)
    """
    # 0) Fresh hybrid snapshot from upload / parsing
    hybrid_snapshot = st.session_state.get("hybrid_resume_snapshot")
    if isinstance(hybrid_snapshot, dict):
        return hybrid_snapshot

    # 1) Legacy: whatever the upload page stored as resume_data
    snapshot = st.session_state.get("resume_data")
    if isinstance(snapshot, dict):
        return snapshot

    # 2) Optional future: call ResumeService here, if we want parity with UMarketU
    return None


def load_job_index(user) -> pd.DataFrame:
    """
    Load the job index visible to this user.

    Priority:
    1. Backend IO_LAYER: /users/{user.id}/jobs/index
    2. ai_data / ai_data_final: jobs/*.json

    No dummy data. If nothing is configured, we show an empty state.
    """
    # 1) Backend
    if IO_LAYER is not None:
        try:
            payload = IO_LAYER.get_json(f"/users/{user.id}/jobs/index")
            return pd.DataFrame(payload or [])
        except Exception:
            pass

    # 2) ai_data fallback
    candidate_root = AI_DATA_DIR / "jobs"
    candidates = list(candidate_root.glob("*.json"))
    if not candidates:
        return pd.DataFrame()

    try:
        raw = json.loads(candidates[0].read_text(encoding="utf-8"))
        return pd.DataFrame(raw or [])
    except Exception:
        return pd.DataFrame()


# ============================================================================
#  FIT ANALYSIS & RESUME TUNING
# ============================================================================

def compute_fit(
    resume_snapshot: Dict[str, Any], job_row: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute a match / focus analysis between the resume and a single job.

    This is the heart of "You marketing you":
    - Where are you strong vs the JD?
    - Where are the obvious gaps?
    - What are the keywords you should emphasise?

    Priority:
    1. AIScoringService.score_resume_against_job()
    2. Deterministic keyword overlap
    """
    if AI_SERVICE_AVAILABLE:
        try:
            return ai_service.score_resume_against_job(resume_snapshot, job_row)
        except Exception:
            pass

    # --- Fallback: simple deterministic overlap -----------------------------

    resume_kw = set(extract_resume_keywords(resume_snapshot))
    jd_kw = set(
        k.strip().lower()
        for k in (job_row.get("keywords") or [])
        if isinstance(k, str)
    )

    if not jd_kw:
        text = " ".join(
            str(job_row.get(col, "")) for col in ("description", "summary", "title")
        )
        jd_kw = {
            w.lower()
            for w in text.replace("/", " ").replace(",", " ").split()
            if len(w) > 3
        }

    overlap = resume_kw & jd_kw
    missing = jd_kw - resume_kw
    score = 0 if not jd_kw else round(100 * len(overlap) / max(1, len(jd_kw)))

    return {
        "score": score,
        "overlap_keywords": sorted(overlap),
        "missing_keywords": sorted(missing),
        "top_strengths": sorted(overlap)[:10],
        "top_gaps": sorted(missing)[:10],
    }


def tune_resume_for_job(
    resume_snapshot: Dict[str, Any], job_row: Dict[str, Any], fit: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a tuned, job-aware resume representation.

    Priority:
    1. AIScoringService.tune_resume_for_job()
    2. Fallback: embed tuning_notes (score, gaps, strengths) into the snapshot

    This is your "tailored CV" engine: we do not render DOCX/PDF here – we
    produce an AI-ready JSON that other modules can export or rebuild as a
    rendered resume.
    """
    if AI_SERVICE_AVAILABLE:
        try:
            return ai_service.tune_resume_for_job(resume_snapshot, job_row, fit)
        except Exception:
            pass

    # Fallback – don't lose intelligence; annotate snapshot with tuning_notes
    tuned = dict(resume_snapshot)
    tuned.setdefault("tuning_notes", {})
    tuned["tuning_notes"][job_row.get("id") or job_row.get("external_id", "")] = {
        "score": fit["score"],
        "gaps": fit["top_gaps"],
        "strengths": fit["top_strengths"],
    }
    return tuned


# ============================================================================
#  APPLICATION TRACKER
# ============================================================================

APPLICATION_STATUSES = [
    "Not started",
    "Applied",
    "Screening",
    "Interview booked",
    "Offer",
    "Rejected",
    "On hold",
]


def _load_applications(user) -> List[Dict[str, Any]]:
    """
    Load application tracker entries.

    Priority:
    1. Cached in session_state["umarketu_state"]["applications"]
    2. Backend IO_LAYER: /users/{user.id}/umarketu/applications
    3. Local JSON file: user_silo/umarketu_applications.json
    """
    state = _get_state()
    if state.get("applications"):
        return state["applications"]

    # 1) Backend
    if IO_LAYER is not None:
        try:
            data = IO_LAYER.get_json(f"/users/{user.id}/umarketu/applications")
            state["applications"] = data or []
            _set_state(state)
            return state["applications"]
        except Exception:
            pass

    # 2) Local file
    silo = _get_user_silo(user)
    tracker_path = silo["root"] / "umarketu_applications.json"
    if tracker_path.exists():
        try:
            data = json.loads(tracker_path.read_text(encoding="utf-8"))
            state["applications"] = data or []
            _set_state(state)
            return state["applications"]
        except Exception:
            pass

    state["applications"] = []
    _set_state(state)
    return state["applications"]


def _persist_applications(user, applications: List[Dict[str, Any]]) -> None:
    """
    Persist application tracker entries both locally and to backend (if present).
    """
    state = _get_state()
    state["applications"] = applications
    _set_state(state)

    # Local JSON
    silo = _get_user_silo(user)
    silo["root"].mkdir(parents=True, exist_ok=True)
    tracker_path = silo["root"] / "umarketu_applications.json"
    tracker_path.write_text(json.dumps(applications, indent=2), encoding="utf-8")

    # Backend
    if IO_LAYER is not None:
        try:
            IO_LAYER.post_json(
                f"/users/{user.id}/umarketu/applications", json_payload=applications
            )
        except Exception:
            pass

def _prepare_fit_for_application(user, app: Dict[str, Any]) -> None:
    """
    Ensure umarketu_state has selected_job / fit_analysis / tuned_resume
    for the given application so Coaching Hub can show full context.

    Strategy:
    - Try to recover the full job row from the user's job index
      using job_id first, then (title, company) as a fallback.
    - If we can't find it, build a minimal job stub from the application.
    - Compute fit + tuned resume and store them in umarketu_state.
    """
    state = _get_state()
    resume_snapshot = load_master_resume_snapshot(user)
    if not resume_snapshot:
        return  # nothing sensible to compute

    jobs_df = load_job_index(user)
    job_row_dict: Optional[Dict[str, Any]] = None

    if isinstance(jobs_df, pd.DataFrame) and not jobs_df.empty:
        job_id = app.get("job_id")

        # 1) Primary: exact id match (if present in DataFrame)
        if job_id is not None and "id" in jobs_df.columns:
            matches = jobs_df[jobs_df["id"] == job_id]
            if not matches.empty:
                job_row_dict = matches.iloc[0].to_dict()

        # 2) Fallback: title + company match
        if job_row_dict is None:
            title = str(app.get("title", "")).strip()
            company = str(app.get("company", "")).strip()
            if title and company and {"title", "company"} <= set(jobs_df.columns):
                subset = jobs_df[
                    (jobs_df["title"].astype(str).str.strip() == title)
                    & (jobs_df["company"].astype(str).str.strip() == company)
                ]
                if not subset.empty:
                    job_row_dict = subset.iloc[0].to_dict()

    # 3) Final fallback – stub job from application data
    if job_row_dict is None:
        job_row_dict = {
            "id": app.get("job_id"),
            "title": app.get("title"),
            "company": app.get("company"),
            "location": app.get("location"),
            "source": app.get("source", "Unknown"),
            "summary": "",
            "description": "",
            "keywords": [],
        }

    fit = compute_fit(resume_snapshot, job_row_dict)
    tuned = tune_resume_for_job(resume_snapshot, job_row_dict, fit)

    state["selected_job"] = job_row_dict
    state["fit_analysis"] = fit
    state["tuned_resume"] = tuned
    _set_state(state)

def _add_application_from_job(
    user,
    job_row: Dict[str, Any],
    fit: Optional[Dict[str, Any]] = None,
    tuned: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Create a new tracker entry from a selected job.

    Mirrors your original UMarketU "send this job to tracker" behaviour.
    """
    applications = _load_applications(user)

    # Avoid duplicates for same job + source
    already = [
        a
        for a in applications
        if a.get("job_id") == job_row.get("id")
        and a.get("source") == job_row.get("source")
    ]
    if already:
        st.info("This job is already in your Application Tracker.")
        return

    new_app = {
        "id": f"app_{len(applications)+1}",
        "job_id": job_row.get("id"),
        "title": job_row.get("title"),
        "company": job_row.get("company"),
        "location": job_row.get("location"),
        "source": job_row.get("source", "Unknown"),
        "status": "Not started",
        "created_at": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
        "fit_score": (fit or {}).get("score"),
        "has_tuned_resume": bool(tuned),
    }
    applications.append(new_app)
    _persist_applications(user, applications)
    st.success("Added to Application Tracker ✅")


# ============================================================================
#  PARTNER MODE (DUAL-CAREER)
# ============================================================================

def _load_partner_resume_snapshot(user) -> Optional[Dict[str, Any]]:
    """
    Load partner resume snapshot from user silo.

    Intentionally **not inferred**: we only use this if the user has explicitly
    uploaded a partner CV, and we have parsed it into partner_resume_ai.json.
    """
    silo = _get_user_silo(user)
    partner_json = silo["root"] / "partner_resume_ai.json"
    if not partner_json.exists():
        return None
    try:
        return json.loads(partner_json.read_text(encoding="utf-8"))
    except Exception:
        return None


def _handle_partner_upload(user) -> Optional[Dict[str, Any]]:
    """
    Entry point for Partner Mode:
    - Allow upload of partner CV (PDF / DOCX)
    - Parse via ResumeService
    - Save as partner_resume_ai.json in user silo
    """
    uploaded = st.file_uploader(
        "Upload your partner's resume (PDF / DOCX)",
        type=["pdf", "docx"],
        key="partner_upload",
    )
    if not uploaded:
        return _load_partner_resume_snapshot(user)

    if not RESUME_SERVICE_AVAILABLE:
        st.warning(
            "The resume parsing service is not available – contact admin if this "
            "should be enabled."
        )
        return None

    with st.spinner("Parsing partner resume…"):
        parsed = resume_service.parse_uploaded_file(uploaded, owner=f"{user.id}-partner")

    if not parsed:
        st.error("We couldn't parse that file – try a different format.")
        return None

    # Save AI-ready copy
    silo = _get_user_silo(user)
    silo["root"].mkdir(parents=True, exist_ok=True)
    out_path = silo["root"] / "partner_resume_ai.json"
    out_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

    st.success("Partner resume parsed and saved for dual-career planning.")
    return parsed


# ============================================================================
#  SMALL UI HELPERS
# ============================================================================

def _render_match_meter(score: Optional[int]) -> None:
    if score is None:
        st.metric("Fit score", value="–")
        return

    st.metric("Fit score", f"{score} / 100")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"thickness": 0.3},
            },
        )
    )
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _render_keyword_buckets(fit: Dict[str, Any]) -> None:
    cols = st.columns(2)
    with cols[0]:
        st.subheader("Strong overlap")
        for kw in fit.get("top_strengths", []):
            st.write(f"✅ {kw}")
    with cols[1]:
        st.subheader("Gaps / opportunities")
        for kw in fit.get("top_gaps", []):
            st.write(f"➕ {kw}")


# ============================================================================
#  PAGE SETUP
# ============================================================================

st.set_page_config(
    page_title="UMarketU – You marketing you",
    page_icon="🧭",
    layout="wide",
)

user = get_current_user()
if not user:
    st.error("You need to be logged in to use UMarketU.")
    st.stop()

ensure_user_folder(user)

state = _get_state()
applications = _load_applications(user)

st.title("🧭 UMarketU – You marketing you")

# ---------------------------------------------------------------------------
# TOP SUMMARY STRIP (PROFILE / RESUME / APPLICATIONS / TOKENS)
# ---------------------------------------------------------------------------

summary_cols = st.columns(4)
with summary_cols[0]:
    st.caption("Profile completeness")
    if USER_DATA_SERVICE_AVAILABLE:
        pc = user_data_service.get_profile_completion(user.id)
        st.metric("Profile", f"{pc.get('percent', 0)}%")
    else:
        st.metric("Profile", "–")

with summary_cols[1]:
    st.caption("Resume data in system")
    snap = load_master_resume_snapshot(user)
    if snap:
        st.metric("Parsed resumes", len(snap.get("raw_files", ["active"])))
    else:
        st.metric("Parsed resumes", "0")

with summary_cols[2]:
    st.caption("Applications tracked")
    st.metric("Applications", len(applications))

with summary_cols[3]:
    st.caption("Token usage")
    if TOKEN_MANAGER_AVAILABLE:
        tokens = token_manager.get_token_summary(user.id)
        st.metric("Today", tokens.get("today", 0))
    else:
        st.metric("Today", "–")

st.divider()

# ============================================================================
#  TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🔍 Job discovery",
        "🎯 Fit analysis",
        "🧬 Resume tuning",
        "📊 Application tracker",
        "🎤 Interview coach",
        "🤝 Partner mode",
    ]
)

# ---------------------------------------------------------------------------
# TAB 1 – JOB DISCOVERY
# ---------------------------------------------------------------------------

with tab1:
    st.subheader("Discover roles that match your skills")

    resume_snapshot = load_master_resume_snapshot(user)
    if not resume_snapshot:
        st.warning(
            "We need a parsed resume to match against jobs. "
            "Upload your latest CV on the **Resume Upload & Analysis** page first."
        )
        if st.button("Open Resume Upload & Analysis"):
            st.switch_page("pages/09_Resume_Upload_Analysis.py")
        st.stop()

    jobs_df = load_job_index(user)

    if jobs_df.empty:
        st.info(
            "There are no jobs available in your personal job index yet. "
            "When the admin or backend populate this, they will appear here."
        )
    else:
        with st.expander("Filters", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                location = st.text_input("Location contains", "")
            with col_b:
                # Kept for future use if you want to pre-filter by approx fit score
                min_score_filter = st.slider(
                    "Minimum fit score (approx, used in later steps)", 0, 100, 50
                )
            with col_c:
                company_filter = st.text_input("Company contains", "")

        filtered = jobs_df.copy()
        if location:
            filtered = filtered[
                filtered["location"].astype(str).str.contains(location, case=False)
            ]
        if company_filter:
            filtered = filtered[
                filtered["company"].astype(str).str.contains(
                    company_filter, case=False
                )
            ]

        st.caption(f"{len(filtered)} roles after filters")

        for _, row in filtered.head(50).iterrows():
            job_dict = row.to_dict()
            with st.container(border=True):
                st.markdown(
                    f"**{job_dict.get('title','(no title)')}**  \n"
                    f"{job_dict.get('company','Unknown')} – "
                    f"{job_dict.get('location','Unknown')}"
                )
                st.caption(job_dict.get("summary") or job_dict.get("description", ""))

                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button(
                        "Analyse fit",
                        key=f"analyse_{row.name}",
                    ):
                        fit = compute_fit(resume_snapshot, job_dict)
                        tuned = tune_resume_for_job(resume_snapshot, job_dict, fit)
                        state = _get_state()
                        state["selected_job"] = job_dict
                        state["fit_analysis"] = fit
                        state["tuned_resume"] = tuned
                        _set_state(state)
                        st.success("Updated fit analysis & tuned resume.")
                with c2:
                    if st.button(
                        "Add to tracker",
                        key=f"add_{row.name}",
                    ):
                        fit = state.get("fit_analysis") or compute_fit(
                            resume_snapshot, job_dict
                        )
                        tuned = state.get("tuned_resume")
                        _add_application_from_job(user, job_dict, fit, tuned)
                with c3:
                    st.caption(
                        f"Source: {job_dict.get('source','Unknown')} – "
                        f"ID: {job_dict.get('id','–')}"
                    )

# ---------------------------------------------------------------------------
# TAB 2 – FIT ANALYSIS
# ---------------------------------------------------------------------------

with tab2:
    st.subheader("Fit analysis for the selected role")

    resume_snapshot = load_master_resume_snapshot(user)
    selected_job = state.get("selected_job")
    fit = state.get("fit_analysis")

    if not resume_snapshot or not selected_job:
        st.info(
            "Pick a role in **Job discovery** and click **Analyse fit** to see "
            "your overlap here."
        )
        st.stop()

    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown(
            f"### {selected_job.get('title','(no title)')} – "
            f"{selected_job.get('company','Unknown')}"
        )
        st.caption(selected_job.get("location", ""))
    with cols[1]:
        _render_match_meter(fit.get("score"))

    _render_keyword_buckets(fit)

    with st.expander("Raw overlap data"):
        st.json(fit)

# ---------------------------------------------------------------------------
# TAB 3 – RESUME TUNING
# ---------------------------------------------------------------------------

with tab3:
    st.subheader("Tuned resume for this role")

    resume_snapshot = load_master_resume_snapshot(user)
    selected_job = state.get("selected_job")
    tuned = state.get("tuned_resume")

    if not resume_snapshot or not selected_job or not tuned:
        st.info(
            "Use **Job discovery → Analyse fit** first. "
            "That will generate a tuned resume for the chosen role."
        )
        st.stop()

    st.caption("This JSON is AI-ready and can be rendered/exported in multiple formats.")
    st.json(tuned)

    st.markdown("---")
    st.markdown("#### Export")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if st.button("Export tuned resume as JSON file"):
            silo = _get_user_silo(user)
            out_path = silo["root"] / "tuned_resume.json"
            out_path.write_text(json.dumps(tuned, indent=2), encoding="utf-8")
            st.success(f"Saved to {out_path}")
    with export_col2:
        if st.button("Promote tuned version as active resume"):
            if RESUME_SERVICE_AVAILABLE:
                resume_service.promote_tuned_resume(user.id, tuned)
                st.success("Tuned resume promoted as the active version.")
            else:
                st.warning(
                    "Backend resume promotion service not available – contact admin."
                )

# ---------------------------------------------------------------------------
# TAB 4 – APPLICATION TRACKER
# ---------------------------------------------------------------------------

with tab4:
    st.subheader("Application tracker")

    applications = _load_applications(user)
    if not applications:
        st.info("No applications yet. Add some from **Job discovery**.")
    else:
        df = pd.DataFrame(applications)
        df_display = df[
            [
                "title",
                "company",
                "location",
                "status",
                "fit_score",
                "created_at",
                "last_updated",
            ]
        ]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("#### Update a single application")
        choices = {
            f"{row['title']} – {row['company']} ({row['status']})": row["id"]
            for row in applications
        }
        selection = st.selectbox(
            "Select application to update", ["—"] + list(choices.keys())
        )
        if selection != "—":
            app_id = choices[selection]
            app = next(a for a in applications if a["id"] == app_id)
            new_status = st.selectbox(
                "Status",
                APPLICATION_STATUSES,
                index=APPLICATION_STATUSES.index(app["status"]),
            )
            note = st.text_area(
                "Internal note (optional)",
                value=app.get("note", ""),
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Save changes"):
                    app["status"] = new_status
                    app["note"] = note
                    app["last_updated"] = datetime.utcnow().isoformat()
                    _persist_applications(user, applications)
                    st.success("Updated.")
            with col_b:
                if st.button("🎤 Prepare interview in Coaching Hub"):
                    _prepare_fit_for_application(user, app)
                    state = _get_state()
                    state["selected_application_for_coach"] = app_id
                    _set_state(state)
                    st.session_state["coaching_entrypoint"] = "interview-from-tracker"
                    st.switch_page("pages/11_Coaching_Hub.py")

# ---------------------------------------------------------------------------
# TAB 5 – INTERVIEW COACH (ROUTER)
# ---------------------------------------------------------------------------

with tab5:
    st.header("🎤 Interview coach")
    st.markdown(
        "UMarketU now routes all interview preparation into the **Coaching Hub**, "
        "so your practice, reflections, and growth plans live in one place."
    )

    st.info(
        "Use this tab to open the Coaching Hub with your current job and resume "
        "context carried across."
    )

    state = _get_state()
    selected_job = state.get("selected_job")
    fit = state.get("fit_analysis")
    tuned = state.get("tuned_resume")

    with st.expander("Current context snapshot", expanded=True):
        if not selected_job:
            st.write("No job selected yet. Choose a role in **Job discovery** first.")
        else:
            st.markdown(
                f"**Role:** {selected_job.get('title','–')}  \n"
                f"**Company:** {selected_job.get('company','–')}"
            )
            if fit:
                strengths = ", ".join(fit.get("top_strengths", [])[:5]) or "–"
                gaps = ", ".join(fit.get("top_gaps", [])[:5]) or "–"
                st.markdown(
                    f"- Match score: **{fit.get('score','–')}**  \n"
                    f"- Strong areas: {strengths}  \n"
                    f"- Gaps: {gaps}"
                )
            if tuned:
                st.caption(
                    "A tuned resume version is available and will be used by the "
                    "Coaching Hub where relevant."
                )

    if st.button("Open Coaching Hub – Interview coach", type="primary"):
        st.session_state["coaching_entrypoint"] = "interview"
        st.switch_page("pages/11_Coaching_Hub.py")

    st.caption(
        "Tip: also use the **Application tracker** tab to jump into the Coaching Hub "
        "from a specific application."
    )

# ---------------------------------------------------------------------------
# TAB 6 – PARTNER MODE
# ---------------------------------------------------------------------------

with tab6:
    st.header("🤝 Partner mode – dual-career planning")

    st.markdown(
        "Many big moves (relocation, industry pivots, flexible working) affect "
        "both you and your partner. Partner mode lets you upload a partner resume "
        "and explore alignment at a high level."
    )

    partner_snapshot = _handle_partner_upload(user)

    if not partner_snapshot:
        st.info(
            "Upload a partner resume to see comparative insights. "
            "Nothing is inferred without explicit upload."
        )
        st.stop()

    resume_snapshot = load_master_resume_snapshot(user)
    if not resume_snapshot:
        st.warning("We still need *your* resume parsed to compare paths.")
        st.stop()

    col_me, col_partner = st.columns(2)
    with col_me:
        st.subheader("You")
        st.write(resume_snapshot.get("headline") or "No headline")
        st.caption(
            ", ".join(extract_resume_keywords(resume_snapshot)[:20]) or "No keywords"
        )
    with col_partner:
        st.subheader("Partner")
        st.write(partner_snapshot.get("headline") or "No headline")
        st.caption(
            ", ".join(extract_resume_keywords(partner_snapshot)[:20]) or "No keywords"
        )

    st.markdown("### Overlap & divergence")
    me_kw = set(extract_resume_keywords(resume_snapshot))
    partner_kw = set(extract_resume_keywords(partner_snapshot))

    overlap = sorted(me_kw & partner_kw)
    only_me = sorted(me_kw - partner_kw)
    only_partner = sorted(partner_kw - me_kw)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Shared skills")
        for kw in overlap[:25]:
            st.write(f"✅ {kw}")
    with c2:
        st.caption("Unique to you")
        for kw in only_me[:25]:
            st.write(f"🧑‍💼 {kw}")
    with c3:
        st.caption("Unique to partner")
        for kw in only_partner[:25]:
            st.write(f"🧑‍🤝‍🧑 {kw}")

    st.caption(
        "This is deliberately high-level. Detailed partner-aware coaching can live "
        "in future Coaching / Mentorship modules once the data is available."
    )
