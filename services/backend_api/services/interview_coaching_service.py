"""
Interview Coaching Service — Role Detection & Question Serving
==============================================================

Provides:
1. Hybrid role function detection (auto-detect from job/resume + user confirm)
2. Role-specific question serving from database
3. 90-day plan generation and customization
4. Session tracking and feedback collection

Uses taxonomy + NLP for intelligent role classification.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger("careertrojan.interview_coaching")


# ─── Role Function Codes ────────────────────────────────────────────────────
ROLE_FUNCTIONS = {
    "marketing": "Marketing",
    "technical": "Technical (IT & Infrastructure)",
    "development": "Development (Software Engineering)",
    "finance": "Finance",
    "sales": "Sales",
    "engineering": "Engineering (Hardware/Mechanical/Manufacturing)",
    "management": "Management",
}

# Classification keywords for auto-detection
ROLE_CLASSIFICATION_KEYWORDS = {
    "marketing": {
        "titles": [
            "marketing manager", "brand manager", "digital marketing", "content strategist",
            "social media manager", "seo specialist", "growth hacker", "demand generation",
            "marketing coordinator", "communications manager", "product marketing",
        ],
        "skills": [
            "seo", "sem", "google analytics", "hubspot", "marketo", "content marketing",
            "social media", "branding", "campaign management", "marketing automation",
            "cac", "customer acquisition", "lead generation", "copywriting",
        ],
    },
    "technical": {
        "titles": [
            "it manager", "systems administrator", "network engineer", "devops engineer",
            "site reliability", "infrastructure engineer", "security analyst",
            "cloud architect", "platform engineer", "it support", "helpdesk",
        ],
        "skills": [
            "aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ansible",
            "linux", "windows server", "networking", "firewalls", "iac",
            "ci/cd", "monitoring", "incident response", "sre",
        ],
    },
    "development": {
        "titles": [
            "software engineer", "software developer", "frontend developer",
            "backend developer", "full stack developer", "mobile developer",
            "web developer", "application developer", "programmer", "coder",
        ],
        "skills": [
            "python", "javascript", "typescript", "java", "c#", "react", "angular",
            "node.js", "django", "flask", "sql", "nosql", "git", "agile", "scrum",
            "rest api", "graphql", "microservices", "unit testing",
        ],
    },
    "finance": {
        "titles": [
            "financial analyst", "accountant", "controller", "cfo", "finance manager",
            "treasury analyst", "fp&a", "auditor", "tax specialist", "bookkeeper",
            "credit analyst", "investment analyst", "risk analyst",
        ],
        "skills": [
            "financial modeling", "excel", "erp", "sap", "oracle financials",
            "gaap", "ifrs", "budgeting", "forecasting", "variance analysis",
            "audit", "tax", "compliance", "reconciliation", "month-end close",
        ],
    },
    "sales": {
        "titles": [
            "sales representative", "account executive", "sales manager",
            "business development", "sales director", "account manager",
            "inside sales", "outside sales", "sales engineer", "solution consultant",
        ],
        "skills": [
            "crm", "salesforce", "hubspot", "cold calling", "prospecting",
            "negotiation", "closing", "pipeline management", "quota",
            "lead qualification", "demo", "presentation", "relationship building",
        ],
    },
    "engineering": {
        "titles": [
            "mechanical engineer", "electrical engineer", "hardware engineer",
            "manufacturing engineer", "process engineer", "quality engineer",
            "design engineer", "cad engineer", "production engineer",
            "plant engineer", "maintenance engineer", "reliability engineer",
        ],
        "skills": [
            "cad", "solidworks", "autocad", "catia", "plm", "fea", "cfd",
            "manufacturing", "six sigma", "lean", "quality control", "gd&t",
            "prototyping", "bom", "dfm", "dfa", "iso 9001",
        ],
    },
    "management": {
        "titles": [
            "manager", "director", "vp", "vice president", "head of", "lead",
            "team lead", "supervisor", "chief", "ceo", "coo", "cto",
            "general manager", "department head", "project manager",
        ],
        "skills": [
            "leadership", "team management", "people management", "strategy",
            "budgeting", "hiring", "performance review", "okr", "kpi",
            "stakeholder management", "executive communication", "vision",
            "change management", "coaching", "mentoring",
        ],
    },
}


class InterviewCoachingService:
    """
    Core service for interview coaching functionality.
    
    Provides:
    - Role function detection from job/resume context
    - Question retrieval by role and category
    - 90-day plan template serving and customization
    - Session management
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._taxonomy_engine = None

    def _get_taxonomy_engine(self):
        """Lazy-load taxonomy engine for role classification."""
        if self._taxonomy_engine is None:
            try:
                from services.backend_api.services.industry_taxonomy_service import TaxonomyService
                self._taxonomy_engine = TaxonomyService()
            except ImportError:
                logger.warning("TaxonomyService not available, using keyword-only detection")
        return self._taxonomy_engine

    # ─── Role Detection ─────────────────────────────────────────────────────

    def detect_role_function(
        self,
        job_title: Optional[str] = None,
        job_description: Optional[str] = None,
        resume_skills: Optional[List[str]] = None,
        resume_experience: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Auto-detect role function from job/resume context.
        
        Returns:
            {
                "detected_function": "development",
                "display_name": "Development (Software Engineering)",
                "confidence": 0.85,
                "signals": {"title_match": "software engineer", "skill_matches": ["python", "react"]},
                "alternatives": [{"code": "technical", "confidence": 0.45}],
                "requires_confirmation": True
            }
        """
        scores: Dict[str, float] = {code: 0.0 for code in ROLE_FUNCTIONS}
        signals: Dict[str, Any] = {"title_matches": [], "skill_matches": [], "keyword_matches": []}

        # Score based on job title
        if job_title:
            title_lower = job_title.lower()
            for code, keywords in ROLE_CLASSIFICATION_KEYWORDS.items():
                for title_kw in keywords.get("titles", []):
                    if title_kw in title_lower:
                        scores[code] += 3.0  # High weight for title match
                        signals["title_matches"].append((code, title_kw))

        # Score based on job description keywords
        if job_description:
            desc_lower = job_description.lower()
            for code, keywords in ROLE_CLASSIFICATION_KEYWORDS.items():
                for skill in keywords.get("skills", []):
                    if skill in desc_lower:
                        scores[code] += 0.5
                        signals["keyword_matches"].append((code, skill))

        # Score based on resume skills
        if resume_skills:
            skills_lower = [s.lower() for s in resume_skills]
            for code, keywords in ROLE_CLASSIFICATION_KEYWORDS.items():
                for skill in keywords.get("skills", []):
                    if skill in skills_lower:
                        scores[code] += 1.0
                        signals["skill_matches"].append((code, skill))

        # Score based on resume experience titles
        if resume_experience:
            for exp in resume_experience[:5]:  # Last 5 roles
                exp_title = (exp.get("title") or exp.get("job_title") or "").lower()
                for code, keywords in ROLE_CLASSIFICATION_KEYWORDS.items():
                    for title_kw in keywords.get("titles", []):
                        if title_kw in exp_title:
                            scores[code] += 2.0

        # Normalize scores to confidence
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            confidences = {code: score / max_score for code, score in scores.items()}
        else:
            confidences = {code: 0.0 for code in scores}

        # Sort by confidence
        sorted_codes = sorted(confidences.items(), key=lambda x: x[1], reverse=True)
        top_code, top_confidence = sorted_codes[0] if sorted_codes else ("management", 0.0)

        # Determine if confirmation is needed
        requires_confirmation = top_confidence < 0.6 or (
            len(sorted_codes) > 1 and sorted_codes[1][1] > 0.4
        )

        return {
            "detected_function": top_code,
            "display_name": ROLE_FUNCTIONS.get(top_code, top_code),
            "confidence": round(top_confidence, 2),
            "signals": signals,
            "alternatives": [
                {"code": code, "display_name": ROLE_FUNCTIONS.get(code, code), "confidence": round(conf, 2)}
                for code, conf in sorted_codes[1:4]
                if conf > 0.1
            ],
            "requires_confirmation": requires_confirmation,
        }

    # ─── Question Serving ───────────────────────────────────────────────────

    def get_questions_for_role(
        self,
        role_function: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve interview questions for a role function.
        
        Args:
            role_function: Code like "development", "sales", etc.
            category: Filter by category (e.g., "Closing", "90-Day", "Good vs Great")
            difficulty: Filter by difficulty level
            limit: Max questions to return
            
        Returns:
            List of question dicts with text, purpose, framework, etc.
        """
        if not self.db:
            # Return in-memory questions if no DB
            return self._get_hardcoded_questions(role_function, category, limit)

        from services.backend_api.db.models import InterviewQuestionBank, RoleFunctionDefinition

        query = (
            self.db.query(InterviewQuestionBank)
            .join(RoleFunctionDefinition)
            .filter(
                RoleFunctionDefinition.function_code == role_function,
                InterviewQuestionBank.is_active == True,
            )
        )

        if category:
            query = query.filter(InterviewQuestionBank.question_category == category)
        if difficulty:
            query = query.filter(InterviewQuestionBank.difficulty_level == difficulty)

        questions = query.order_by(InterviewQuestionBank.effectiveness_score.desc()).limit(limit).all()

        return [
            {
                "id": q.id,
                "text": q.question_text,
                "category": q.question_category,
                "purpose": q.question_purpose,
                "sample_framework": q.sample_answer_framework,
                "interviewer_insight": q.interviewer_insight,
                "difficulty": q.difficulty_level,
                "tags": q.tags or [],
                "source": q.source_attribution,
            }
            for q in questions
        ]

    def _get_hardcoded_questions(
        self, role_function: str, category: Optional[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback questions when DB is unavailable."""
        # Universal questions that apply to any role
        universal = [
            {
                "id": 1,
                "text": "Thinking back to people who have held this position previously, what differentiated the ones who were good from the ones who were truly great?",
                "category": "Good vs Great",
                "purpose": "Uncover the hidden success criteria beyond the job description",
                "sample_framework": "Listen carefully, then connect your strengths to their 'great' criteria",
                "interviewer_insight": "Shows strategic thinking and desire to excel, not just meet expectations",
                "difficulty": "advanced",
                "tags": ["closing", "strategic", "high-impact"],
                "source": "Harvard Business Review",
            },
            {
                "id": 2,
                "text": "What is the single most important thing I should accomplish in my first 90 days to make you feel like you made the right hire?",
                "category": "90-Day",
                "purpose": "Get explicit success criteria for your first quarter",
                "sample_framework": "Frame your follow-up around their specific answer",
                "interviewer_insight": "Demonstrates accountability and results-orientation",
                "difficulty": "standard",
                "tags": ["closing", "90-day", "expectations"],
                "source": "The Muse",
            },
            {
                "id": 3,
                "text": "From what we've discussed today, which of my skills or experiences do you feel would be the most immediate asset to your team?",
                "category": "Closing",
                "purpose": "Forces interviewer to vocalize your strengths (locks them into pro-hire mindset)",
                "sample_framework": "Ask confidently at the end of the interview",
                "interviewer_insight": "Bold move that shows confidence — use when rapport is high",
                "difficulty": "advanced",
                "tags": ["closing", "bold", "seal-the-deal"],
                "source": "Reddit Career Advice",
            },
            {
                "id": 4,
                "text": "Is there anything in my background that gives you pause about my fit for this role?",
                "category": "Closing",
                "purpose": "Final chance to address concerns before you leave",
                "sample_framework": "Listen without defensiveness, address directly",
                "interviewer_insight": "Shows self-awareness and openness to feedback",
                "difficulty": "standard",
                "tags": ["closing", "objection-handling", "strategic"],
                "source": "Quora",
            },
            {
                "id": 5,
                "text": "If you could snap your fingers and fix one thing about the company or the team right now, what would it be?",
                "category": "Culture",
                "purpose": "Uncover real challenges and pain points",
                "sample_framework": "Connect your experience to helping solve that problem",
                "interviewer_insight": "Reveals honesty and gives you leverage to position yourself as solution",
                "difficulty": "standard",
                "tags": ["culture", "reality-check", "problems"],
                "source": "Reddit",
            },
        ]

        # Role-specific questions
        role_specific = {
            "development": [
                {
                    "id": 101,
                    "text": "How does the team protect developers from meeting bloat to ensure they get the 'flow state' time needed for complex coding?",
                    "category": "Role-specific",
                    "purpose": "Assess engineering culture and respect for deep work",
                    "sample_framework": "Mention your preferred focus time practices",
                    "interviewer_insight": "Shows you understand productivity drivers",
                    "difficulty": "standard",
                    "tags": ["development", "culture", "productivity"],
                    "source": "arc.dev",
                },
                {
                    "id": 102,
                    "text": "What is the average time between a PR being merged and the code reaching production? What is the main blocker in that pipeline?",
                    "category": "Role-specific",
                    "purpose": "Understand deployment maturity and bottlenecks",
                    "sample_framework": "Share your experience improving deployment velocity",
                    "interviewer_insight": "Shows DevOps awareness",
                    "difficulty": "standard",
                    "tags": ["development", "devops", "process"],
                    "source": "Tech Interview Handbook",
                },
            ],
            "sales": [
                {
                    "id": 201,
                    "text": "What are you doing as a manager to help the 'middle 60%' of your sales team hit their targets, rather than just relying on the top 10%?",
                    "category": "Role-specific",
                    "purpose": "Assess coaching culture and realistic expectations",
                    "sample_framework": "Share how you've improved with coaching",
                    "interviewer_insight": "Shows team awareness, not just individual focus",
                    "difficulty": "standard",
                    "tags": ["sales", "coaching", "team"],
                    "source": "Tech Interview Handbook",
                },
            ],
            "finance": [
                {
                    "id": 301,
                    "text": "What was the biggest variance in last year's budget, and what did it reveal about the company's operational assumptions?",
                    "category": "Role-specific",
                    "purpose": "Show analytical thinking and business acumen",
                    "sample_framework": "Connect to your experience with variance analysis",
                    "interviewer_insight": "Demonstrates you think beyond numbers",
                    "difficulty": "advanced",
                    "tags": ["finance", "analysis", "strategic"],
                    "source": "Corporate Finance Institute",
                },
            ],
            "marketing": [
                {
                    "id": 401,
                    "text": "How do you currently balance long-term brand building with the need for short-term, data-driven performance results?",
                    "category": "Role-specific",
                    "purpose": "Understand marketing philosophy and metrics focus",
                    "sample_framework": "Share your experience balancing both",
                    "interviewer_insight": "Shows strategic marketing understanding",
                    "difficulty": "standard",
                    "tags": ["marketing", "strategy", "metrics"],
                    "source": "Reddit Marketing",
                },
            ],
            "engineering": [
                {
                    "id": 501,
                    "text": "How do you balance the pressure for rapid prototyping with the long-term need for product durability and lifecycle support?",
                    "category": "Role-specific",
                    "purpose": "Assess engineering maturity and quality focus",
                    "sample_framework": "Share examples of balancing speed vs quality",
                    "interviewer_insight": "Shows systems thinking",
                    "difficulty": "standard",
                    "tags": ["engineering", "quality", "lifecycle"],
                    "source": "Corporate Finance Institute",
                },
            ],
            "management": [
                {
                    "id": 601,
                    "text": "Tell me about a time you coached a low performer back to high performance. What specific support did you provide?",
                    "category": "Role-specific",
                    "purpose": "Assess leadership style and people development",
                    "sample_framework": "Use STAR method with specific interventions",
                    "interviewer_insight": "Shows coaching ability, not just authority",
                    "difficulty": "standard",
                    "tags": ["management", "coaching", "leadership"],
                    "source": "Tech Interview Handbook",
                },
            ],
            "technical": [
                {
                    "id": 701,
                    "text": "Beyond standard technical debt, what is the most costly technical decision made early on that the team is still living with today?",
                    "category": "Role-specific",
                    "purpose": "Understand legacy challenges and learning culture",
                    "sample_framework": "Share how you've managed technical debt",
                    "interviewer_insight": "Shows architectural awareness",
                    "difficulty": "standard",
                    "tags": ["technical", "architecture", "legacy"],
                    "source": "Tech Interview Handbook",
                },
            ],
        }

        # Combine universal + role-specific
        all_questions = universal.copy()
        if role_function in role_specific:
            all_questions.extend(role_specific[role_function])

        # Filter by category if specified
        if category:
            all_questions = [q for q in all_questions if q["category"] == category]

        return all_questions[:limit]

    # ─── 90-Day Plans ───────────────────────────────────────────────────────

    def get_ninety_day_template(
        self,
        role_function: str,
        seniority: str = "mid",
    ) -> Dict[str, Any]:
        """
        Get 30-60-90 day plan template for a role function.
        """
        if not self.db:
            return self._get_hardcoded_90day_template(role_function, seniority)

        from services.backend_api.db.models import NinetyDayPlanTemplate, RoleFunctionDefinition

        template = (
            self.db.query(NinetyDayPlanTemplate)
            .join(RoleFunctionDefinition)
            .filter(
                RoleFunctionDefinition.function_code == role_function,
                NinetyDayPlanTemplate.seniority_level == seniority,
                NinetyDayPlanTemplate.is_active == True,
            )
            .first()
        )

        if not template:
            return self._get_hardcoded_90day_template(role_function, seniority)

        return {
            "id": template.id,
            "role_function": role_function,
            "seniority": seniority,
            "name": template.template_name,
            "focus_areas": template.focus_areas,
            "day_30": {
                "actions": template.day_30_actions,
                "success_metric": template.day_30_success_metric,
            },
            "day_60": {
                "actions": template.day_60_actions,
                "success_metric": template.day_60_success_metric,
            },
            "day_90": {
                "actions": template.day_90_actions,
                "success_metric": template.day_90_success_metric,
            },
            "smart_reports": template.smart_reports,
            "closing_statement": template.closing_statement,
        }

    def _get_hardcoded_90day_template(self, role_function: str, seniority: str) -> Dict[str, Any]:
        """Fallback templates when DB is unavailable."""
        templates = {
            "development": {
                "name": "Software Development 30-60-90",
                "focus_areas": {
                    "day_30": "Codebase Absorption",
                    "day_60": "Feature Ownership",
                    "day_90": "Technical Leadership",
                },
                "day_30": {
                    "actions": [
                        "Complete all onboarding and environment setup",
                        "Shadow 3 senior developers on different parts of the codebase",
                        "Submit first PR (bug fix or small feature)",
                        "Document one area of architectural confusion",
                    ],
                    "success_metric": "Ship first production code; document top 3 codebase pain points",
                },
                "day_60": {
                    "actions": [
                        "Own 1-2 features from ticket to production",
                        "Participate in code reviews (give and receive)",
                        "Identify one technical debt item and propose fix",
                        "Pair program with team members across stack",
                    ],
                    "success_metric": "Deliver first feature independently; propose one process improvement",
                },
                "day_90": {
                    "actions": [
                        "Lead a sprint item end-to-end",
                        "Mentor a newer team member",
                        "Present a technical deep-dive to the team",
                        "Contribute to architectural decisions",
                    ],
                    "success_metric": "Full velocity; recognized as go-to for at least one area",
                },
                "smart_reports": {
                    "day_30": "Onboarding Reflection + Tech Stack Assessment",
                    "day_60": "First Feature Post-Mortem + Tech Debt Audit",
                    "day_90": "6-Month Technical Roadmap Proposal",
                },
                "closing_statement": "What one specific result in 90 days would make you feel like you made a great hire?",
            },
            "sales": {
                "name": "Sales Professional 30-60-90",
                "focus_areas": {
                    "day_30": "Pipeline Absorption",
                    "day_60": "Deal Ownership",
                    "day_90": "Quota Contribution",
                },
                "day_30": {
                    "actions": [
                        "Complete product training and certifications",
                        "Shadow 5+ sales calls with top performers",
                        "Learn CRM inside and out",
                        "Build territory map and target list",
                    ],
                    "success_metric": "Complete certifications; have 20+ qualified leads in pipeline",
                },
                "day_60": {
                    "actions": [
                        "Run solo discovery calls",
                        "Close first deal",
                        "Implement re-engagement strategy for stale leads",
                        "Develop 3 case studies from existing customers",
                    ],
                    "success_metric": "First closed deal; demo-to-close ratio improvement plan",
                },
                "day_90": {
                    "actions": [
                        "Hit monthly quota",
                        "Build referral network",
                        "Train on new product launch",
                        "Contribute feedback to product team",
                    ],
                    "success_metric": "On track for quarterly quota; established client relationships",
                },
                "smart_reports": {
                    "day_30": "Territory Analysis + Competitive Positioning",
                    "day_60": "Funnel Friction Report + First Deal Analysis",
                    "day_90": "Q2 Pipeline Strategy + Win/Loss Analysis",
                },
                "closing_statement": "What's the #1 metric I should be focused on to prove ROI in 90 days?",
            },
            "management": {
                "name": "People Manager 30-60-90",
                "focus_areas": {
                    "day_30": "Team Absorption",
                    "day_60": "Process Optimization",
                    "day_90": "Strategic Leadership",
                },
                "day_30": {
                    "actions": [
                        "Complete 1-on-1 'listening tour' with every direct report",
                        "Review last 12 months of performance data",
                        "Understand current KPIs and how they're tracked",
                        "Identify top 3 team pain points",
                    ],
                    "success_metric": "Complete team assessment; identify one quick win",
                },
                "day_60": {
                    "actions": [
                        "Implement first process improvement",
                        "Resolve at least one 'blocker' per team member",
                        "Establish clear communication cadence",
                        "Set 90-day goals with each team member",
                    ],
                    "success_metric": "Measurable productivity improvement; team trust established",
                },
                "day_90": {
                    "actions": [
                        "Present strategic roadmap to leadership",
                        "Identify hiring/development gaps",
                        "Implement performance recognition program",
                        "Build cross-functional relationships",
                    ],
                    "success_metric": "Team velocity increase; clear 6-month plan approved",
                },
                "smart_reports": {
                    "day_30": "Team Capability Matrix + Pain Point Summary",
                    "day_60": "Process Improvement Results + Engagement Pulse",
                    "day_90": "6-Month Strategic Plan + Hiring Roadmap",
                },
                "closing_statement": "What would success look like for this team in 6 months, and what's blocking it now?",
            },
        }

        # Default template for unspecified roles
        default = {
            "name": f"{ROLE_FUNCTIONS.get(role_function, role_function)} 30-60-90",
            "focus_areas": {
                "day_30": "Absorption",
                "day_60": "Application",
                "day_90": "Ownership",
            },
            "day_30": {
                "actions": [
                    "Complete all mandatory training",
                    "1-on-1s with key stakeholders",
                    "Learn tools and processes",
                    "Document top 3 pain points",
                ],
                "success_metric": "Full onboarding complete; first contribution delivered",
            },
            "day_60": {
                "actions": [
                    "Own first project/deliverable",
                    "Propose one process improvement",
                    "Build cross-functional relationships",
                    "Deliver first 'quick win'",
                ],
                "success_metric": "First project delivered; measurable improvement proposed",
            },
            "day_90": {
                "actions": [
                    "Lead high-priority initiative",
                    "Present roadmap to leadership",
                    "Mentor/support team members",
                    "Full velocity achieved",
                ],
                "success_metric": "Operating at full capacity; strategic plan approved",
            },
            "smart_reports": {
                "day_30": "Onboarding Reflection",
                "day_60": "Quick Win Post-Mortem",
                "day_90": "Strategic Roadmap",
            },
            "closing_statement": "If you were to grade my performance A-F at 90 days, what one result would earn me that A?",
        }

        template = templates.get(role_function, default)
        return {
            "id": None,
            "role_function": role_function,
            "seniority": seniority,
            **template,
        }


# ─── Module-level convenience functions ─────────────────────────────────────

_service: Optional[InterviewCoachingService] = None


def get_interview_coaching_service(db: Optional[Session] = None) -> InterviewCoachingService:
    """Get or create the interview coaching service instance."""
    global _service
    if _service is None or db is not None:
        _service = InterviewCoachingService(db=db)
    return _service


def detect_role_function(
    job_title: Optional[str] = None,
    job_description: Optional[str] = None,
    resume_skills: Optional[List[str]] = None,
    resume_experience: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Convenience function for role detection."""
    return get_interview_coaching_service().detect_role_function(
        job_title=job_title,
        job_description=job_description,
        resume_skills=resume_skills,
        resume_experience=resume_experience,
    )


def get_interview_questions(
    role_function: str,
    category: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Convenience function for question retrieval."""
    return get_interview_coaching_service().get_questions_for_role(
        role_function=role_function,
        category=category,
        limit=limit,
    )


def get_90day_plan(role_function: str, seniority: str = "mid") -> Dict[str, Any]:
    """Convenience function for 90-day plan template."""
    return get_interview_coaching_service().get_ninety_day_template(
        role_function=role_function,
        seniority=seniority,
    )
