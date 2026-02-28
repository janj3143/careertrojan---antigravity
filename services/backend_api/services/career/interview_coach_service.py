from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Tuple

from services.shared.paths import CareerTrojanPaths


ROLE_KEYWORDS: Dict[str, List[str]] = {
    "marketing": [
        "marketing", "brand", "campaign", "cac", "seo", "sem", "content", "attribution", "channel",
    ],
    "technical": [
        "infrastructure", "network", "cloud", "security", "devops", "incident", "uptime", "iac", "compliance",
    ],
    "development": [
        "software", "developer", "engineering manager", "code", "api", "backend", "frontend", "microservice", "deployment", "pr",
    ],
    "finance": [
        "finance", "budget", "forecast", "variance", "erp", "audit", "p&l", "reconciliation", "cashflow",
    ],
    "sales": [
        "sales", "pipeline", "quota", "deal", "territory", "crm", "prospect", "closing", "revenue",
    ],
    "engineering": [
        "mechanical", "hardware", "manufacturing", "cad", "prototype", "safety", "quality", "production", "vendor",
    ],
    "management": [
        "manager", "leadership", "team", "stakeholder", "retention", "performance", "strategy", "roadmap", "coaching",
    ],
}


ROLE_SPECIFIC_QUESTIONS: Dict[str, List[str]] = {
    "marketing": [
        "How do you balance long-term brand building with short-term performance targets in this role?",
        "What is the biggest bottleneck in your current marketing stack, and how should this role address it?",
        "Which channel is currently under-leveraged, and what evidence supports changing spend there?",
        "How does customer feedback move from insights into campaign decisions here?",
    ],
    "technical": [
        "What early technical decision creates the highest operational cost today, and how are you addressing it?",
        "How are post-mortems run after incidents: blame-focused or learning-focused?",
        "Where are you on the automation journey from manual ops to Infrastructure as Code?",
        "How do you balance deployment speed against security/compliance requirements?",
    ],
    "development": [
        "What is the average lead time from PR merge to production, and what is the biggest blocker?",
        "How does the team protect deep work time for engineers?",
        "How much autonomy do developers have to propose architecture changes?",
        "Tell me about a failed engineering experiment and what leadership learned from it.",
    ],
    "finance": [
        "What was the biggest budget variance last year, and what did it reveal about assumptions?",
        "Where is finance still relying on manual spreadsheets that should be automated?",
        "How has finance evolved from reporting to strategic advising in this organization?",
        "Which external risk would matter most for this role over the next 12 months?",
    ],
    "sales": [
        "How do you coach the middle 60% of reps to quota consistently?",
        "At what stage are reps encouraged to disqualify weak deals?",
        "How long is realistic ramp-up for this territory, and what blocks new reps most?",
        "Can you share a recent product improvement driven by field sales feedback?",
    ],
    "engineering": [
        "How do you balance rapid prototyping with durability and lifecycle support?",
        "Can you describe a time safety or quality concerns paused delivery, and how leadership responded?",
        "Where does friction usually appear between design and manufacturing teams?",
        "How has supply-chain volatility changed vendor and material strategy?",
    ],
    "management": [
        "What support process do you use to coach a low performer back to high performance?",
        "How do you convert company strategy into daily team priorities people can execute?",
        "What skill gap are you hoping this hire closes in the first two quarters?",
        "How do you protect the team when priorities shift mid-quarter?",
    ],
}


CORE_HIGH_IMPACT_QUESTIONS: List[str] = [
    "From what we have discussed, which of my skills would be the most immediate asset to your team?",
    "Is there anything in my background that gives you pause about my fit for this role?",
    "Thinking about people who succeeded in this role, what separates good from truly great?",
    "What is the single most important result I should deliver in the first 90 days for you to feel this was the right hire?",
    "Are there daily challenges in this role that are not visible in the official job description?",
    "Can you share a project that did not go as planned and what the team changed afterward?",
    "What is one question I have not asked that is critical for success in this role?",
]


_LEARNING_LOCK = Lock()


def _learning_store_path() -> Path:
    paths = CareerTrojanPaths()
    return paths.ai_data_final / "interview_learning.json"


def _load_learning_store() -> Dict[str, Any]:
    path = _learning_store_path()
    if not path.exists():
        return {
            "meta": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "version": 1,
            },
            "question_feedback": {},
            "answer_feedback": {},
            "role_performance": {},
        }
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {
            "meta": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "version": 1,
            },
            "question_feedback": {},
            "answer_feedback": {},
            "role_performance": {},
        }


def _save_learning_store(store: Dict[str, Any]) -> None:
    path = _learning_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    store.setdefault("meta", {})["updated_at"] = datetime.utcnow().isoformat() + "Z"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2, ensure_ascii=False)


def _question_key(role_family: str, question_type: str, question: str) -> str:
    return f"{role_family}::{question_type.strip().lower()}::{question.strip().lower()}"


def _score_question_with_learning(store: Dict[str, Any], role_family: str, question_type: str, question: str) -> float:
    key = _question_key(role_family, question_type, question)
    feedback = store.get("question_feedback", {}).get(key) or {}
    helpful = float(feedback.get("helpful", 0))
    not_helpful = float(feedback.get("not_helpful", 0))
    total = helpful + not_helpful
    if total <= 0:
        return 0.5
    return helpful / total


def record_interview_feedback(
    *,
    role_family: str,
    question_type: str,
    question: str,
    answer_score: int | None = None,
    helpful: bool | None = None,
    session_outcome: str | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    with _LEARNING_LOCK:
        store = _load_learning_store()

        key = _question_key(role_family, question_type, question)
        q_feedback = store.setdefault("question_feedback", {}).setdefault(
            key,
            {
                "role_family": role_family,
                "question_type": question_type,
                "question": question,
                "helpful": 0,
                "not_helpful": 0,
                "last_seen": None,
            },
        )

        if helpful is True:
            q_feedback["helpful"] = int(q_feedback.get("helpful", 0)) + 1
        elif helpful is False:
            q_feedback["not_helpful"] = int(q_feedback.get("not_helpful", 0)) + 1
        q_feedback["last_seen"] = datetime.utcnow().isoformat() + "Z"

        if answer_score is not None:
            answer_bucket = store.setdefault("answer_feedback", {}).setdefault(
                role_family,
                {"count": 0, "score_sum": 0, "avg_score": 0},
            )
            answer_bucket["count"] = int(answer_bucket.get("count", 0)) + 1
            answer_bucket["score_sum"] = int(answer_bucket.get("score_sum", 0)) + int(answer_score)
            answer_bucket["avg_score"] = round(
                answer_bucket["score_sum"] / max(answer_bucket["count"], 1),
                2,
            )

        if session_outcome:
            role_perf = store.setdefault("role_performance", {}).setdefault(
                role_family,
                {"total": 0, "interview_pass": 0, "offer": 0, "other": 0},
            )
            role_perf["total"] = int(role_perf.get("total", 0)) + 1
            outcome = session_outcome.strip().lower()
            if outcome == "interview_pass":
                role_perf["interview_pass"] = int(role_perf.get("interview_pass", 0)) + 1
            elif outcome == "offer":
                role_perf["offer"] = int(role_perf.get("offer", 0)) + 1
            else:
                role_perf["other"] = int(role_perf.get("other", 0)) + 1

        if user_id:
            store.setdefault("meta", {})["last_feedback_user"] = str(user_id)

        _save_learning_store(store)

        return {
            "status": "ok",
            "role_family": role_family,
            "question_type": question_type,
            "question": question,
            "learning_score": _score_question_with_learning(store, role_family, question_type, question),
        }


def get_learning_profile(role_family: str | None = None) -> Dict[str, Any]:
    store = _load_learning_store()
    role_scores = store.get("answer_feedback", {})
    role_perf = store.get("role_performance", {})

    if role_family:
        return {
            "role_family": role_family,
            "answer_feedback": role_scores.get(role_family, {}),
            "performance": role_perf.get(role_family, {}),
            "updated_at": (store.get("meta") or {}).get("updated_at"),
        }

    return {
        "roles": role_scores,
        "performance": role_perf,
        "updated_at": (store.get("meta") or {}).get("updated_at"),
    }


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9\-\+]{2,}", text.lower())


def _context_text(resume: Dict[str, Any] | None, job: Dict[str, Any] | None) -> Tuple[str, str]:
    resume = resume or {}
    job = job or {}

    resume_parts: List[str] = []
    job_parts: List[str] = []

    for key in ("raw_text", "content", "full_text", "summary", "headline"):
        value = resume.get(key)
        if isinstance(value, str):
            resume_parts.append(value)

    for key in ("title", "target_role"):
        value = resume.get(key)
        if isinstance(value, str):
            resume_parts.append(value)

    for key in ("skills",):
        value = resume.get(key)
        if isinstance(value, list):
            resume_parts.extend([str(v) for v in value if isinstance(v, (str, int, float))])

    for key in ("title", "description", "full_text", "jd_text", "role"):
        value = job.get(key)
        if isinstance(value, str):
            job_parts.append(value)

    return "\n".join(resume_parts), "\n".join(job_parts)


def infer_role_family(resume: Dict[str, Any] | None, job: Dict[str, Any] | None) -> str:
    resume_text, job_text = _context_text(resume, job)
    text = f"{resume_text}\n{job_text}".lower()

    scores: Dict[str, int] = {}
    for family, keywords in ROLE_KEYWORDS.items():
        scores[family] = sum(1 for keyword in keywords if keyword in text)

    if not scores:
        return "management"

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] == 0:
        return "management"
    return ranked[0][0]


def _missing_keywords(resume: Dict[str, Any] | None, job: Dict[str, Any] | None, limit: int = 6) -> List[str]:
    resume_text, job_text = _context_text(resume, job)
    resume_tokens = set(_tokenize(resume_text))
    job_tokens = _tokenize(job_text)
    if not job_tokens:
        return []

    freq = Counter(job_tokens)
    common_missing: List[str] = []
    for token, _ in freq.most_common(50):
        if token not in resume_tokens and len(token) > 3:
            common_missing.append(token)
        if len(common_missing) >= limit:
            break
    return common_missing


def generate_interview_questions(
    *,
    question_type: str,
    count: int,
    resume: Dict[str, Any] | None = None,
    job: Dict[str, Any] | None = None,
    fit: Dict[str, Any] | None = None,
) -> List[str]:
    role_family = infer_role_family(resume, job)
    missing = _missing_keywords(resume, job)
    store = _load_learning_store()

    questions: List[str] = []

    normalized = (question_type or "").strip().lower()
    explicit_role_section = normalized in {
        "marketing",
        "technical",
        "development",
        "finance",
        "sales",
        "engineering",
        "management",
    }

    if explicit_role_section:
        questions.extend(ROLE_SPECIFIC_QUESTIONS.get(normalized, []))
        questions.append(
            "What one result in my first 90 days would most clearly prove I am succeeding in this role?"
        )
    elif "role" in normalized:
        questions.extend(ROLE_SPECIFIC_QUESTIONS.get(role_family, []))
        questions.append(
            "If you graded my performance at day 90 from A to F, what one outcome would earn an A in this role?"
        )
    elif "leadership" in normalized:
        questions.extend(ROLE_SPECIFIC_QUESTIONS["management"])
    elif "culture" in normalized:
        questions.extend([
            "If you could fix one thing about team culture today, what would it be?",
            "What usually surprises new hires after they join this team?",
            "How has the company changed most in the past year?",
            "When someone is struggling, how do managers support them in practice?",
        ])
    elif "problem" in normalized:
        questions.extend([
            "Tell me about a recent project that missed target. What changed afterward?",
            "Where does friction usually happen between teams for this role?",
            "What part of the delivery pipeline is least predictable today?",
            "What failure mode in this role would have the highest business impact?",
        ])
    else:
        questions.extend(CORE_HIGH_IMPACT_QUESTIONS)

    questions.extend(CORE_HIGH_IMPACT_QUESTIONS)

    if missing:
        questions.append(
            f"I noticed this role emphasizes {', '.join(missing[:3])}. Which of these is truly mandatory in the first 90 days?"
        )

    if fit and isinstance(fit, dict):
        top_gaps = fit.get("top_gaps") or []
        if isinstance(top_gaps, list) and top_gaps:
            gap_terms = [str(item) for item in top_gaps[:3]]
            questions.append(
                f"Your fit analysis highlights {', '.join(gap_terms)}. Which one should I close first to maximize impact?"
            )

    deduped: List[str] = []
    seen = set()
    for question in questions:
        key = question.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(question)

    ranked = sorted(
        deduped,
        key=lambda q: _score_question_with_learning(store, role_family, question_type, q),
        reverse=True,
    )

    return ranked[: max(1, min(count, 20))]


def review_interview_answer(
    *,
    question: str,
    answer: str,
    resume: Dict[str, Any] | None = None,
    job: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    answer_text = (answer or "").strip()
    word_count = len(answer_text.split())

    has_s = bool(re.search(r"\bsituation\b", answer_text, flags=re.IGNORECASE))
    has_t = bool(re.search(r"\btask\b", answer_text, flags=re.IGNORECASE))
    has_a = bool(re.search(r"\baction\b", answer_text, flags=re.IGNORECASE))
    has_r = bool(re.search(r"\bresult\b", answer_text, flags=re.IGNORECASE))
    star_hits = sum([has_s, has_t, has_a, has_r])

    has_metrics = bool(re.search(r"\b\d+\b|\d+%|\$\d+", answer_text))
    ownership_hits = len(re.findall(r"\b(i led|i built|i improved|i reduced|i increased|i delivered|i owned)\b", answer_text, flags=re.IGNORECASE))

    _, job_text = _context_text(resume, job)
    job_terms = [t for t in _tokenize(job_text) if len(t) > 4]
    answer_terms = set(_tokenize(answer_text))
    aligned_terms = len({t for t in job_terms[:40] if t in answer_terms}) if job_terms else 0

    suggestions: List[str] = []

    if word_count < 80:
        suggestions.append("Expand the answer to around 90-140 words so the interviewer sees context, action, and impact.")
    if star_hits < 2:
        suggestions.append("Use a clearer STAR structure: include Situation, Task, Action, and measurable Result.")
    if not has_metrics:
        suggestions.append("Add one concrete metric (%, time saved, revenue, cost, quality, or cycle-time improvement).")
    if ownership_hits == 0:
        suggestions.append("Use stronger ownership language (for example: 'I led', 'I implemented', 'I delivered').")
    if aligned_terms < 2 and job_terms:
        suggestions.append("Mirror more role language from the job description to improve perceived fit.")

    score = 100
    score -= 20 if word_count < 60 else 0
    score -= 15 if star_hits < 2 else 0
    score -= 15 if not has_metrics else 0
    score -= 10 if ownership_hits == 0 else 0
    score -= 10 if aligned_terms < 2 and job_terms else 0
    score = max(45, min(100, score))

    if score >= 85:
        summary = "Strong answer: clear structure and solid credibility signals."
    elif score >= 70:
        summary = "Good baseline answer with room to sharpen impact and specificity."
    else:
        summary = "Promising direction, but it needs clearer structure and measurable outcomes."

    if not suggestions:
        suggestions.append("For your next pass, tighten to one concise story with one high-impact metric.")

    return {
        "summary": summary,
        "score": score,
        "suggestions": suggestions,
        "signals": {
            "word_count": word_count,
            "star_elements_detected": star_hits,
            "has_metrics": has_metrics,
            "ownership_language_hits": ownership_hits,
            "job_alignment_terms": aligned_terms,
        },
    }


def generate_star_stories(
    *,
    focus_areas: List[str],
    resume: Dict[str, Any] | None = None,
    job: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    resume = resume or {}
    job = job or {}

    role = str(job.get("title") or resume.get("target_role") or "the role")
    skills = resume.get("skills") if isinstance(resume.get("skills"), list) else []
    primary_skill = str(skills[0]) if skills else "core domain skill"

    stories: List[Dict[str, str]] = []
    for area in focus_areas[:6]:
        area_name = str(area).strip() or "impact"
        stories.append(
            {
                "title": f"{area_name.title()} impact story",
                "situation": f"In a previous role, the team had a challenge around {area_name.lower()} while targeting outcomes for {role}.",
                "task": "I was asked to stabilize delivery and improve measurable business outcomes.",
                "action": f"I prioritized root-cause analysis, used {primary_skill}, aligned stakeholders, and implemented a focused improvement plan.",
                "result": "We reduced delays and improved performance metrics in a way leadership could track week by week.",
            }
        )

    if not stories:
        stories.append(
            {
                "title": "First 90-day ownership story",
                "situation": f"A new hire entering {role} needed to prove early value.",
                "task": "Define and deliver one high-impact result in the first 90 days.",
                "action": "Mapped team blockers, aligned on one measurable objective, and executed with weekly checkpoints.",
                "result": "Delivered a visible quick win and built trust through transparent progress metrics.",
            }
        )

    return stories
