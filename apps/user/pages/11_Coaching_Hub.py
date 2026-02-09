def _generate_questions(
	resume_snapshot: Optional[Dict[str, Any]],
	job: Optional[Dict[str, Any]],
	fit: Optional[Dict[str, Any]],
	question_type: str,
	count: int = 10,
) -> List[str]:
	"""
	Generate interview questions, preferring the hybrid engine.
	No fallback content is generated.
	"""
	payload = {
		"question_type": question_type,
		"count": count,
	}

	if resume_snapshot:
		payload["resume"] = resume_snapshot
	if job:
		payload["job"] = job
	if fit:
		payload["fit"] = fit

	# 1) Hybrid engine
	if HYBRID_ENGINE_AVAILABLE:
		try:
			q = hybrid_engine.generate_interview_questions(payload)
			if isinstance(q, list):
				return [str(item) for item in q]
		except Exception:
			pass

	# 2) Legacy AI service
	if AI_SERVICE_AVAILABLE:
		try:
			q = ai_service.generate_interview_questions(payload)
			if isinstance(q, list):
				return [str(item) for item in q]
		except Exception:
			pass

	return []


def _review_answer(
	resume_snapshot: Optional[Dict[str, Any]],
	job: Optional[Dict[str, Any]],
	question: str,
	answer: str,
) -> Dict[str, Any]:
	"""
	Provide feedback on an interview answer.

	Priority:
	1) HybridCareerEngine.review_interview_answer
	2) AIScoringService.review_interview_answer
	3) No fallback feedback
	"""
	payload = {
		"question": question,
		"answer": answer,
	}
	if resume_snapshot:
		payload["resume"] = resume_snapshot
	if job:
		payload["job"] = job

	# 1) Hybrid engine
	if HYBRID_ENGINE_AVAILABLE:
		try:
			fb = hybrid_engine.review_interview_answer(payload)
			if isinstance(fb, dict):
				fb.setdefault("engine", "hybrid-career-engine")
				return fb
		except Exception:
			pass

	# 2) Legacy AI service
	if AI_SERVICE_AVAILABLE:
		try:
			fb = ai_service.review_interview_answer(payload)
			if isinstance(fb, dict):
				fb.setdefault("engine", "ai-scoring-service")
				return fb
		except Exception:
			pass

	return {
		"summary": "Feedback unavailable (no AI engine configured).",
		"suggestions": [],
		"engine": "unavailable",
	}


def _generate_star_stories(
	resume_snapshot: Optional[Dict[str, Any]],
	job: Optional[Dict[str, Any]],
	focus_areas: List[str],
) -> List[Dict[str, str]]:
	"""
	Generate STAR-style stories for coaching and answer prep.

	Output list items are dicts like:
		{
			"title": "...",
			"situation": "...",
			"task": "...",
			"action": "...",
			"result": "..."
		}
	"""
	payload = {
		"focus_areas": focus_areas,
	}
	if resume_snapshot:
		payload["resume"] = resume_snapshot
	if job:
		payload["job"] = job

	# 1) Hybrid engine
	if HYBRID_ENGINE_AVAILABLE:
		try:
			stories = hybrid_engine.generate_star_stories(payload)
			if isinstance(stories, list):
				return [s for s in stories if isinstance(s, dict)]
		except Exception:
			pass

	# 2) Legacy AI service
	if AI_SERVICE_AVAILABLE:
		try:
			stories = ai_service.generate_star_stories(payload)
			if isinstance(stories, list):
				return [s for s in stories if isinstance(s, dict)]
		except Exception:
			pass

	return []


# ============================================================================
#  PAGE SETUP
# ============================================================================

st.set_page_config(
	page_title="Coaching Hub – Interview & Growth",
	page_icon="🎤",
	layout="wide",
)

user = get_current_user()
if not user:
	st.error("You need to be logged in to use the Coaching Hub.")
	st.stop()

ensure_user_folder(user)

entrypoint = st.session_state.get("coaching_entrypoint", "direct")
resume_snapshot = _load_resume_snapshot(user)
job_context, fit_context = _load_umarketu_context(user)
application_context = None
if entrypoint == "interview-from-tracker":
	application_context = _load_application_for_coaching(user)

st.title("🎤 Coaching Hub")


# Top strip / context
top_cols = st.columns(3)
with top_cols[0]:
	st.metric("Entry mode", entrypoint)

with top_cols[1]:
	if resume_snapshot:
		kw = _extract_keywords(resume_snapshot)
		st.metric("Resume keywords", len(kw))
	else:
		st.metric("Resume keywords", "0")

with top_cols[2]:
	if TOKEN_MANAGER_AVAILABLE:
		tokens = token_manager.get_token_summary(user.id)
		st.metric("Tokens used today", tokens.get("today", 0))
	else:
		st.metric("Tokens used today", "–")

st.divider()

# ============================================================================
#  TABS
# ============================================================================

tab_overview, tab_questions, tab_practice, tab_star, tab_log = st.tabs(
	[
		"🔎 Overview & context",
		"❓ Interview questions",
		"🗣️ Practise answers",
		"⭐ STAR stories",
		"📓 Reflection log",
	]
)

# ---------------------------------------------------------------------------
# TAB 1 – OVERVIEW & CONTEXT
# ---------------------------------------------------------------------------

with tab_overview:
	st.subheader("Overview & context")

	if resume_snapshot:
		name = resume_snapshot.get("name") or resume_snapshot.get("full_name") or "Candidate"
		headline = resume_snapshot.get("headline") or resume_snapshot.get("title") or ""
		st.markdown(f"**Candidate:** {name}")
		if headline:
			st.caption(headline)
	else:
		st.info(
			"No parsed resume snapshot found yet. "
			"The Coaching Hub will still work, but some features will be less tailored."
		)

	st.markdown("### Current role / application focus")

	if job_context:
		cols = st.columns([2, 1])
		with cols[0]:
			st.markdown(
				f"**Role:** {job_context.get('title','(no title)')}  \n"
				f"**Company:** {job_context.get('company','Unknown')}"
			)
			loc = job_context.get("location") or ""
			if loc:
				st.caption(loc)
		with cols[1]:
			if fit_context and isinstance(fit_context, dict) and "score" in fit_context:
				score = fit_context.get("score")
				st.metric("Fit score", f"{score}/100" if score is not None else "–")
			else:
				st.metric("Fit score", "–")
	elif application_context:
		st.markdown(
			f"**Application:** {application_context.get('title','(no title)')}  \n"
			f"**Company:** {application_context.get('company','Unknown')}"
		)
		st.caption(
			f"Status: {application_context.get('status','Unknown')} – "
			f"Location: {application_context.get('location','Unknown')}"
		)
	else:
		st.info(
			"No specific role context has been passed in. "
			"You can still practise general interview questions."
		)

	if fit_context:
		st.markdown("### Strengths & gaps from UMarketU")
		c1, c2 = st.columns(2)
		with c1:
			st.caption("Top strengths")
			for kw in fit_context.get("top_strengths", [])[:10]:
				st.write(f"✅ {kw}")
		with c2:
			st.caption("Top gaps / opportunities")
			for kw in fit_context.get("top_gaps", [])[:10]:
				st.write(f"➕ {kw}")

	if application_context:
		st.markdown("### Application details (from UMarketU tracker)")
		st.json(application_context)

	if not job_context and not application_context:
		st.markdown(
			"You can create context by visiting **UMarketU → Job discovery** and "
			"running a fit analysis, then re-opening the Coaching Hub from there."
		)

# ---------------------------------------------------------------------------
# TAB 2 – INTERVIEW QUESTIONS
# ---------------------------------------------------------------------------

with tab_questions:
	st.subheader("Interview question generator")

	q_col1, q_col2 = st.columns([2, 1])
	with q_col1:
		q_type = st.selectbox("Question type", QUESTION_TYPES)
	with q_col2:
		q_count = st.slider("Number of questions", min_value=3, max_value=20, value=10)

	if st.button("Generate questions", type="primary"):
		questions = _generate_questions(
			resume_snapshot=resume_snapshot,
			job=job_context,
			fit=fit_context,
			question_type=q_type,
			count=q_count,
		)
		st.session_state["coaching_questions"] = questions
		st.success(f"Generated {len(questions)} questions.")

	questions = st.session_state.get("coaching_questions", [])
	if questions:
		st.markdown("### Suggested questions")
		for i, q in enumerate(questions, start=1):
			st.markdown(f"**Q{i}.** {q}")
	else:
		st.info("Generate a set of questions to start practising.")

# ---------------------------------------------------------------------------
# TAB 3 – PRACTISE ANSWERS
# ---------------------------------------------------------------------------

with tab_practice:
	st.subheader("Practise your answers")

	questions = st.session_state.get("coaching_questions", [])
	default_question = questions[0] if questions else ""

	question = st.text_area(
		"Question",
		value=default_question,
		help="Choose a question from the generated list or type your own.",
	)
	answer = st.text_area(
		"Your answer",
		height=220,
		help="Write your answer in a STAR structure if possible (Situation, Task, Action, Result).",
	)

	col_a, col_b = st.columns([1, 1])
	with col_a:
		review_clicked = st.button("Get coaching feedback", type="primary")
	with col_b:
		log_checkbox = st.checkbox("Save this answer & feedback into my coaching log", value=True)

	if review_clicked:
		if not question.strip() or not answer.strip():
			st.warning("Please provide both a question and an answer to review.")
		else:
			with st.spinner("Reviewing your answer..."):
				feedback = _review_answer(
					resume_snapshot=resume_snapshot,
					job=job_context,
					question=question,
					answer=answer,
				)

			st.markdown("### Feedback")
			summary = feedback.get("summary")
			if summary:
				st.write(summary)

			suggestions = feedback.get("suggestions") or feedback.get("points") or []
			if suggestions:
				st.markdown("#### Suggestions for improvement")
				for s in suggestions:
					st.write(f"• {s}")

			engine_used = feedback.get("engine", "unknown")
			st.caption(f"Feedback engine: {engine_used}")

			if log_checkbox:
				entry = {
					"timestamp": datetime.utcnow().isoformat(),
					"mode": "interview-practice",
					"question": question,
					"answer": answer,
					"feedback": feedback,
					"context": {
						"entrypoint": entrypoint,
						"job": job_context,
						"application": application_context,
					},
				}
				_append_coaching_log(user, entry)
				st.success("Answer and feedback saved to your coaching log.")

# ---------------------------------------------------------------------------
# TAB 4 – STAR STORIES
# ---------------------------------------------------------------------------

with tab_star:
	st.subheader("STAR stories from your experience")

	if resume_snapshot is None:
		st.warning(
			"We need a parsed resume to auto-generate STAR stories. "
			"Upload and parse your resume first."
		)
	else:
		all_kw = _extract_keywords(resume_snapshot)
		default_focus = all_kw[:10]

		selected_focus = st.multiselect(
			"Pick a few focus areas (skills, strengths, themes)",
			options=all_kw,
			default=default_focus,
			help="These guide which stories we prioritise.",
		)

		if st.button("Generate STAR stories", type="primary"):
			with st.spinner("Generating STAR-style stories..."):
				stories = _generate_star_stories(
					resume_snapshot=resume_snapshot,
					job=job_context,
					focus_areas=selected_focus,
				)
			st.session_state["coaching_star_stories"] = stories

		stories = st.session_state.get("coaching_star_stories", [])
		if stories:
			for idx, story in enumerate(stories, start=1):
				with st.expander(f"Story {idx}: {story.get('title','(untitled)')}", expanded=False):
					st.markdown(f"**Situation**  \n{story.get('situation','')}")
					st.markdown(f"**Task**  \n{story.get('task','')}")
					st.markdown(f"**Action**  \n{story.get('action','')}")
					st.markdown(f"**Result**  \n{story.get('result','')}")
					src = story.get("source") or story.get("_tuned_by") or "hybrid/ai"
					st.caption(f"Story source: {src}")
		else:
			st.info("Generate STAR stories to see concrete examples you can reuse in interviews.")

# ---------------------------------------------------------------------------
# TAB 5 – REFLECTION LOG
# ---------------------------------------------------------------------------

with tab_log:
	st.subheader("Coaching reflections & notes")

	log = _load_coaching_log(user)
	if not log:
		st.info("No coaching log entries yet. Practise an answer and tick 'save to log' to start building one.")
	else:
		st.markdown("### Recent entries")
		# Show newest first
		log_df = pd.DataFrame(log)
		log_df_display = log_df[["timestamp", "mode", "question"]].sort_values(
			"timestamp", ascending=False
		)
		st.dataframe(log_df_display, use_container_width=True, hide_index=True)

		st.markdown("### Detailed view")
		selected_idx = st.selectbox(
			"Pick an entry to inspect",
			options=list(range(len(log_df_display))),
			format_func=lambda i: f"{log_df_display.iloc[i]['timestamp']} – {log_df_display.iloc[i]['mode']}",
		)

		# Map back to original log (we used a sorted view)
		selected_ts = log_df_display.iloc[selected_idx]["timestamp"]
		entry = next((e for e in log if e.get("timestamp") == selected_ts), None)
		if entry:
			st.json(entry)

	st.markdown("---")
	st.markdown("#### Add a free-form reflection")

	free_note = st.text_area(
		"Reflection",
		help="Capture insights, patterns, or habits you want to build.",
	)
	if st.button("Save reflection"):
		if not free_note.strip():
			st.warning("Write something before saving.")
		else:
			entry = {
				"timestamp": datetime.utcnow().isoformat(),
				"mode": "free-reflection",
				"note": free_note,
				"context": {
					"entrypoint": entrypoint,
					"job": job_context,
					"application": application_context,
				},
			}
			_append_coaching_log(user, entry)
			st.success("Reflection saved to your coaching log.")

	if str(BASE_DIR) not in sys.path:
		sys.path.insert(0, str(BASE_DIR))
	st.session_state.setdefault("sys_path_added", []).append(str(BASE_DIR))

# --- Shared config & bridges ------------------------------------------------

try:
	from shared.config import USER_PORTAL_DATA_DIR
except Exception:  # pragma: no cover
	USER_PORTAL_DATA_DIR = Path(".")

try:
	from shared.state_bridge import (
		get_current_user,
		ensure_user_folder,
		get_user_silo_paths,
	)
except Exception:  # pragma: no cover

	def get_current_user():
		return None

	def ensure_user_folder(*_, **__):
		return USER_PORTAL_DATA_DIR

	def get_user_silo_paths(*_, **__):
		return {"root": USER_PORTAL_DATA_DIR}


try:
	from shared.io_layer import IO_LAYER
except Exception:  # pragma: no cover
	IO_LAYER = None

# --- Optional services ------------------------------------------------------

# Token usage (for monitoring)
try:
	from token_management_system import init_token_system_for_page

	token_manager = init_token_system_for_page()
	TOKEN_MANAGER_AVAILABLE = True
except Exception:
	token_manager = None
	TOKEN_MANAGER_AVAILABLE = False

# Hybrid AI engine (8-model stack)
try:
	from services.hybrid_ai_engine import HybridCareerEngine

	hybrid_engine = HybridCareerEngine()
	HYBRID_ENGINE_AVAILABLE = True
except Exception:
	hybrid_engine = None
	HYBRID_ENGINE_AVAILABLE = False

# Legacy AI service (compat)
try:
	from services.ai_service import AIScoringService

	ai_service = AIScoringService()
	AI_SERVICE_AVAILABLE = True
except Exception:
	ai_service = None
	AI_SERVICE_AVAILABLE = False

# Resume service
try:
	from services.resume_service import ResumeService

	resume_service = ResumeService()
	RESUME_SERVICE_AVAILABLE = True
except Exception:
	resume_service = None
	RESUME_SERVICE_AVAILABLE = False


# ============================================================================
#  STATE & IO HELPERS
# ============================================================================

COACHING_LOG_FILENAME = "coaching_log.json"


def _get_user_silo(user) -> Dict[str, Path]:
	try:
		return get_user_silo_paths(user)
	except Exception:
		return {"root": USER_PORTAL_DATA_DIR}


def _load_resume_snapshot(user) -> Optional[Dict[str, Any]]:
	"""
	Unified entrypoint for "current resume" inside Coaching Hub.

	Priority:
	0. hybrid_resume_snapshot (from Resume Upload page)
	1. tuned resume passed via UMarketU (if present)
	2. backend ResumeService active snapshot
	3. user_silo / working_copy / ai_json latest JSON
	"""
	# 0) Fresh hybrid snapshot
	hybrid_snapshot = st.session_state.get("hybrid_resume_snapshot")
	if isinstance(hybrid_snapshot, dict):
		return hybrid_snapshot

	# 1) Tuned resume from UMarketU
	um_state = st.session_state.get("umarketu_state", {})
	tuned = um_state.get("tuned_resume")
	if isinstance(tuned, dict):
		return tuned

	# 2) Backend resume service
	if RESUME_SERVICE_AVAILABLE:
		try:
			return resume_service.get_active_resume_snapshot(user.id)
		except Exception:
			pass

	# 3) Fallback – latest ai_json file
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


def _extract_keywords(snapshot: Dict[str, Any]) -> List[str]:
	skills = snapshot.get("skills", []) or []
	kw = {s.strip() for s in skills if isinstance(s, str) and s.strip()}

	for bucket in ("ai_keywords", "inferred_keywords", "hybrid_keywords"):
		for val in snapshot.get(bucket, []) or []:
			if isinstance(val, str) and val.strip():
				kw.add(val.strip())

	return sorted(kw)


def _load_umarketu_context(user) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
	"""
	Load context (job, fit) from UMarketU's state, if present.
	"""
	um_state = st.session_state.get("umarketu_state", {})
	job = um_state.get("selected_job")
	fit = um_state.get("fit_analysis")
	return job, fit


def _load_application_for_coaching(user) -> Optional[Dict[str, Any]]:
	"""
	When called from UMarketU Application Tracker:
	- umarketu_state.selected_application_for_coach -> app_id
	- Optionally fetch full app list from IO_LAYER or user_silo

	We keep this light – just enough to show context in Overview.
	"""
	um_state = st.session_state.get("umarketu_state", {})
	app_id = um_state.get("selected_application_for_coach")
	if not app_id:
		return None

	# 1) Try backend
	if IO_LAYER is not None:
		try:
			data = IO_LAYER.get_json(f"/users/{user.id}/umarketu/applications")
			apps = data or []
		except Exception:
			apps = []
	else:
		# 2) Local file
		silo = _get_user_silo(user)
		tracker_path = silo["root"] / "umarketu_applications.json"
		if tracker_path.exists():
			try:
				apps = json.loads(tracker_path.read_text(encoding="utf-8"))
			except Exception:
				apps = []
		else:
			apps = []

	for app in apps:
		if app.get("id") == app_id:
			return app

	return None


def _load_coaching_log(user) -> List[Dict[str, Any]]:
	silo = _get_user_silo(user)
	log_path = silo["root"] / COACHING_LOG_FILENAME
	if not log_path.exists():
		return []
	try:
		return json.loads(log_path.read_text(encoding="utf-8"))
	except Exception:
		return []


def _append_coaching_log(user, entry: Dict[str, Any]) -> None:
	log = _load_coaching_log(user)
	log.append(entry)
	silo = _get_user_silo(user)
	silo["root"].mkdir(parents=True, exist_ok=True)
	log_path = silo["root"] / COACHING_LOG_FILENAME
	log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")


# ============================================================================
#  HYBRID COACHING FUNCTIONS
# ============================================================================

QUESTION_TYPES = ["General competency", "Role-specific", "Culture & values", "Leadership", "Problem-solving"]


def _generate_questions(
	resume_snapshot: Optional[Dict[str, Any]],
	job: Optional[Dict[str, Any]],
	fit: Optional[Dict[str, Any]],
	question_type: str,
	count: int = 10,
) -> List[str]:
	"""
	Generate interview questions, preferring the hybrid engine.
	Fallback is deterministic templated questions.
	"""
	payload = {
		"question_type": question_type,
		"count": count,
	}

	if resume_snapshot:
		payload["resume"] = resume_snapshot
	if job:
		payload["job"] = job
	if fit:
		payload["fit"] = fit

	# 1) Hybrid engine
	if HYBRID_ENGINE_AVAILABLE:
		try:
			q = hybrid_engine.generate_interview_questions(payload)
			if isinstance(q, list):
				return [str(item) for item in q]
		except Exception:
			pass

	# 2) Legacy AI service
	if AI_SERVICE_AVAILABLE:
		try:
			q = ai_service.generate_interview_questions(payload)
			if isinstance(q, list):
				return [str(item) for item in q]
		except Exception:
			pass

	# 3) Deterministic fallback
	base_questions = {
		"General competency": [
			"Tell me about yourself.",
			"What is your greatest strength?",
			"What is your greatest development area and how are you working on it?",
			"Describe a time you had to adapt to a major change.",
		],
		"Role-specific": [
			"Walk me through a recent project that best reflects your fit for this role.",
			"How do you stay up to date with developments in this field?",
			"Describe a time you solved a role-specific problem from end to end.",
		],
		"Culture & values": [
			"What kind of environment do you do your best work in?",
			"Tell me about a time you contributed to a positive team culture.",
			"Describe a time you disagreed with a decision and how you handled it.",
		],
		"Leadership": [
			"Tell me about a time you led a team through a challenging situation.",
			"How do you motivate others, even when you have no formal authority?",
			"Describe a difficult decision you had to make as a leader.",
		],
		"Problem-solving": [
			"Describe a complex problem you faced and how you approached it.",
			"Tell me about a time something went wrong and you had to fix it quickly.",
			"Walk me through your process for diagnosing and resolving issues.",
		],
	}

	return base_questions.get(question_type, base_questions["General competency"])[:count]

