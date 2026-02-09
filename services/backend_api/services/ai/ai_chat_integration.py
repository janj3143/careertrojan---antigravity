"""
AI Job Title Chat Integration Service
====================================

Provides AI-powered chat functionality for job title descriptions, meanings,
and career insights. Integrates with various AI services and maintains a
knowledge base of job title information.

Author: IntelliCV-AI Team
Date: October 2, 2025
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

# Optional shared backend: Google-first, Exa-fallback web lookup.
try:
    from shared_backend.services.web_search_orchestrator import two_tier_web_search  # type: ignore
except Exception:
    two_tier_web_search = None  # type: ignore

# Optional knowledge-hole queue (async resolution)
try:
    from shared_backend.queue.knowledge_hole_queue import get_knowledge_hole_queue_manager  # type: ignore
except Exception:
    get_knowledge_hole_queue_manager = None  # type: ignore

# Try to import AI services (can be expanded with OpenAI, Anthropic, etc.)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIJobTitleChat:
    """AI-powered chat service for job title information"""

    def __init__(self):
        self.knowledge_base = self._load_job_title_knowledge_base()
        self.chat_history = []
        self.response_cache = {}
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Setup logging for chat interactions"""
        logger = logging.getLogger("ai_job_chat")
        logger.setLevel(logging.INFO)

        # Create file handler if logs directory exists
        log_dir = Path("logs")
        if log_dir.exists():
            handler = logging.FileHandler(log_dir / "ai_job_chat.log")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_job_title_knowledge_base(self) -> Dict:
        """Load comprehensive job title knowledge base"""
        try:
            kb_path = Path("ai_data/job_title_knowledge_base.json")
            kb_path.parent.mkdir(parents=True, exist_ok=True)
            if kb_path.exists():
                with open(kb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # No embedded defaults. Start empty and fill only from live sources.
            empty = {"job_titles": {}}
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(empty, f, indent=2, ensure_ascii=False)
            return empty
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return {"job_titles": {}}

    def _create_default_knowledge_base(self) -> Dict:
        """Deprecated: no embedded defaults allowed."""
        return {"job_titles": {}}

    def _persist_job_title(self, normalized_title: str, payload: Dict) -> None:
        try:
            kb_path = Path("ai_data/job_title_knowledge_base.json")
            kb_path.parent.mkdir(parents=True, exist_ok=True)
            kb = self.knowledge_base if isinstance(self.knowledge_base, dict) else {"job_titles": {}}
            kb.setdefault("job_titles", {})
            kb["job_titles"][normalized_title] = payload
            self.knowledge_base = kb
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(kb, f, indent=2, ensure_ascii=False)
        except Exception:
            return

    def _live_lookup_job_title(self, job_title: str) -> Optional[Dict]:
        if not two_tier_web_search:
            return None
        query = f"{job_title} job description responsibilities requirements"
        try:
            res = two_tier_web_search(
                query=query,
                content_type="job_description",
                num_results=5,
                triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat._live_lookup_job_title",
            )
            candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
            top = (candidates or [None])[0]
            if not top:
                return None

            url = top.get("url") or top.get("link")
            text = (top.get("text") or top.get("snippet") or "").strip()
            title = (top.get("title") or "").strip() or job_title

            if not url and not text:
                return None

            # Do not fabricate: store only what we can extract.
            return {
                "meaning": "",
                "description": text[:800] if text else "",
                "key_responsibilities": [],
                "required_skills": [],
                "similar_titles": [],
                "career_progression": [],
                "industry_context": "",
                "sources": [{"title": title, "url": url, "method": res.get("method")}],
                "source": "live_web",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def get_job_title_description(self, job_title: str) -> Dict:
        """Get comprehensive description of a job title"""
        # Normalize job title
        normalized_title = self._normalize_job_title(job_title)

        # Check knowledge base
        if normalized_title in self.knowledge_base["job_titles"]:
            job_info = self.knowledge_base["job_titles"][normalized_title].copy()
            job_info["source"] = "knowledge_base"
            return job_info

        # Not found: perform live lookup (no mock/fallback content).
        live = self._live_lookup_job_title(job_title)
        if live:
            self._persist_job_title(normalized_title, live)
            payload = live.copy()
            payload["original_query"] = job_title
            return payload

        # Record a knowledge hole for asynchronous resolution (no fabricated response).
        try:
            if get_knowledge_hole_queue_manager:
                qm = get_knowledge_hole_queue_manager()
                qm.enqueue_job_title(
                    job_title,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.get_job_title_description",
                    metadata={"normalized_title": normalized_title},
                )
        except Exception:
            pass

        return {
            "meaning": "",
            "description": "",
            "key_responsibilities": [],
            "required_skills": [],
            "similar_titles": [],
            "career_progression": [],
            "industry_context": "",
            "sources": [],
            "source": "unavailable",
            "original_query": job_title,
            "timestamp": datetime.now().isoformat(),
            "error": "No live knowledge base entry and live web lookup unavailable/empty.",
        }

    def chat_about_job_title(self, job_title: str, question: str) -> str:
        """Interactive chat about job title with context-aware responses"""

        # Log the interaction
        self.logger.info(f"Chat query - Title: {job_title}, Question: {question}")

        # Get job title information
        job_info = self.get_job_title_description(job_title)

        # Analyze question intent
        intent = self._analyze_question_intent(question)

        # Generate contextual response using live/KB data only.
        response = self._generate_contextual_response(job_info, question, intent)

        # Store in chat history
        self.chat_history.append({
            "timestamp": datetime.now().isoformat(),
            "job_title": job_title,
            "question": question,
            "intent": intent,
            "response": response
        })

        return response

    def _normalize_job_title(self, title: str) -> str:
        """Normalize job title for matching"""
        # Remove extra spaces, convert to title case
        normalized = re.sub(r'\s+', ' ', title.strip()).title()

        # Handle common variations
        variations = {
            "Software Dev": "Software Developer",
            "Data Sci": "Data Scientist",
            "PM": "Product Manager",
            "SWE": "Software Engineer",
            "ML Engineer": "Machine Learning Engineer"
        }

        return variations.get(normalized, normalized)

    def _find_similar_title(self, title: str) -> Optional[str]:
        """Find similar job title using fuzzy matching"""
        from difflib import SequenceMatcher

        best_match = None
        best_score = 0.6  # Minimum similarity threshold

        for known_title in self.knowledge_base["job_titles"].keys():
            similarity = SequenceMatcher(None, title.lower(), known_title.lower()).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = known_title

        return best_match

    def _analyze_question_intent(self, question: str) -> str:
        """Analyze the intent behind the question"""
        question_lower = question.lower()

        if any(word in question_lower for word in ["salary", "pay", "compensation", "money", "earn"]):
            return "salary"
        elif any(word in question_lower for word in ["skills", "requirements", "qualifications", "need"]):
            return "skills"
        elif any(word in question_lower for word in ["career", "path", "progression", "advancement", "growth"]):
            return "career_path"
        elif any(word in question_lower for word in ["responsibilities", "duties", "tasks", "do", "job"]):
            return "responsibilities"
        elif any(word in question_lower for word in ["similar", "related", "like", "alternative"]):
            return "similar_roles"
        elif any(word in question_lower for word in ["industry", "sector", "field", "market"]):
            return "industry"
        elif any(word in question_lower for word in ["education", "degree", "certification", "study"]):
            return "education"
        else:
            return "general"

    def _generate_contextual_response(self, job_info: Dict, question: str, intent: str) -> str:
        """Generate contextual response based on intent and job information"""

        job_title = job_info.get("original_query", "this role")

        if intent == "salary":
            if two_tier_web_search:
                q = f"{job_title} salary range"
                res = two_tier_web_search(
                    query=q,
                    content_type="generic",
                    num_results=3,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.salary_lookup",
                )
                candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
                top = (candidates or [None])[0]
                snippet = (top or {}).get("text") or (top or {}).get("snippet") or ""
                url = (top or {}).get("url") or (top or {}).get("link") or ""
                if snippet:
                    return f"{snippet}\n\nSource: {url}".strip()
            return "Live salary data not available. Configure Google/Exa and retry."

        elif intent == "skills":
            skills = job_info.get("required_skills", [])
            if skills:
                return "\n".join([f"• {s}" for s in skills[:12]])
            if two_tier_web_search:
                q = f"{job_title} required skills"
                res = two_tier_web_search(
                    query=q,
                    content_type="generic",
                    num_results=3,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.skills_lookup",
                )
                candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
                top = (candidates or [None])[0]
                snippet = (top or {}).get("text") or (top or {}).get("snippet") or ""
                url = (top or {}).get("url") or (top or {}).get("link") or ""
                if snippet:
                    return f"{snippet}\n\nSource: {url}".strip()
            return "No live skills data available. Configure Google/Exa and retry."

        elif intent == "career_path":
            progression = job_info.get("career_progression", [])
            if progression:
                return "\n".join([f"• {r}" for r in progression])
            if two_tier_web_search:
                q = f"{job_title} career progression"
                res = two_tier_web_search(
                    query=q,
                    content_type="generic",
                    num_results=3,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.career_lookup",
                )
                candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
                top = (candidates or [None])[0]
                snippet = (top or {}).get("text") or (top or {}).get("snippet") or ""
                url = (top or {}).get("url") or (top or {}).get("link") or ""
                if snippet:
                    return f"{snippet}\n\nSource: {url}".strip()
            return "No live career path data available. Configure Google/Exa and retry."

        elif intent == "responsibilities":
            responsibilities = job_info.get("key_responsibilities", [])
            if responsibilities:
                return "\n".join([f"• {r}" for r in responsibilities])
            if two_tier_web_search:
                q = f"{job_title} responsibilities"
                res = two_tier_web_search(
                    query=q,
                    content_type="job_description",
                    num_results=3,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.resp_lookup",
                )
                candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
                top = (candidates or [None])[0]
                snippet = (top or {}).get("text") or (top or {}).get("snippet") or ""
                url = (top or {}).get("url") or (top or {}).get("link") or ""
                if snippet:
                    return f"{snippet}\n\nSource: {url}".strip()
            return "No live responsibilities data available. Configure Google/Exa and retry."

        elif intent == "similar_roles":
            similar_titles = job_info.get("similar_titles", [])
            if similar_titles:
                response = f"🔗 **Similar Roles to {job_title}:**\n\n"
                for title in similar_titles:
                    response += f"• {title}\n"

                return response
            else:
                return f"Similar roles to {job_title} would include related positions in the same field or industry with overlapping skills and responsibilities."

        elif intent == "industry":
            industry_context = job_info.get("industry_context", "")
            if industry_context:
                return f"🏢 **Industry Context for {job_title}:**\n\n{industry_context}"
            else:
                return f"{job_title} can be found across various industries, with specific requirements and opportunities varying by sector."

        elif intent == "education":
            return f"📚 **Education for {job_title}:**\n\nEducational requirements vary by employer and experience level. Common paths include relevant bachelor's degree, professional certifications, bootcamps, or equivalent practical experience. Continuous learning and skill development are important for career advancement."

        else:  # general intent
            description = job_info.get("description", "")
            if description:
                return description
            if two_tier_web_search:
                res = two_tier_web_search(
                    query=f"{job_title} job description",
                    content_type="job_description",
                    num_results=3,
                    triggered_from="admin_portal.services.ai_chat_integration.AIJobTitleChat.general_lookup",
                )
                candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
                top = (candidates or [None])[0]
                snippet = (top or {}).get("text") or (top or {}).get("snippet") or ""
                url = (top or {}).get("url") or (top or {}).get("link") or ""
                if snippet:
                    return f"{snippet}\n\nSource: {url}".strip()
            return "No live data available. Configure Google/Exa and retry."

    def _generate_generic_response(self, job_title: str) -> Dict:
        """Generate generic response for unknown job titles"""
        # No generic/fabricated fallback responses allowed.
        return {
            "meaning": "",
            "description": "",
            "key_responsibilities": [],
            "required_skills": [],
            "similar_titles": [],
            "career_progression": [],
            "industry_context": "",
            "sources": [],
            "source": "unavailable",
            "timestamp": datetime.now().isoformat(),
        }

    def get_chat_analytics(self) -> Dict:
        """Get analytics on chat usage and patterns"""
        if not self.chat_history:
            return {"total_chats": 0, "popular_intents": {}, "popular_titles": {}}

        # Analyze chat patterns
        intents = [chat["intent"] for chat in self.chat_history]
        titles = [chat["job_title"] for chat in self.chat_history]

        from collections import Counter

        return {
            "total_chats": len(self.chat_history),
            "popular_intents": dict(Counter(intents).most_common(5)),
            "popular_titles": dict(Counter(titles).most_common(10)),
            "recent_activity": self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history
        }

    def export_knowledge_base(self, file_path: str = "ai_data/job_title_knowledge_export.json"):
        """Export the knowledge base to a file"""
        try:
            export_data = {
                "knowledge_base": self.knowledge_base,
                "chat_history": self.chat_history,
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return f"Knowledge base exported to {file_path}"

        except Exception as e:
            return f"Error exporting knowledge base: {e}"

    def add_job_title_to_knowledge_base(self, job_title: str, job_info: Dict):
        """Add new job title information to knowledge base"""
        self.knowledge_base["job_titles"][job_title] = job_info
        self.logger.info(f"Added new job title to knowledge base: {job_title}")

    def update_job_title_info(self, job_title: str, updates: Dict):
        """Update existing job title information"""
        if job_title in self.knowledge_base["job_titles"]:
            self.knowledge_base["job_titles"][job_title].update(updates)
            self.logger.info(f"Updated job title information: {job_title}")
        else:
            self.logger.warning(f"Job title not found for update: {job_title}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the chat service
    chat_service = AIJobTitleChat()

    # Test job title description
    print("=== Job Title Description Test ===")
    job_info = chat_service.get_job_title_description("Software Engineer")
    print(f"Job Title: Software Engineer")
    print(f"Meaning: {job_info['meaning']}")
    print(f"Similar Titles: {', '.join(job_info['similar_titles'][:3])}")

    # Test interactive chat
    print("\n=== Interactive Chat Test ===")
    response = chat_service.chat_about_job_title("Data Scientist", "What skills do I need?")
    print(f"Question: What skills do I need for Data Scientist?")
    print(f"Response: {response}")

    # Test analytics
    print("\n=== Analytics Test ===")
    analytics = chat_service.get_chat_analytics()
    print(f"Total chats: {analytics['total_chats']}")
    print(f"Popular intents: {analytics['popular_intents']}")
