"""
CareerTrojan — AI Gateway (Control Plane — DEPRECATED)
=======================================================

.. deprecated::
    For new code, use the canonical gateway instead:

        from services.ai_engine.ai_gateway import ai_gateway
        result = ai_gateway.score_candidate(resume_text, skills, ...)

    This control-plane gateway is retained for admin-specific features
    (request logging, cost estimation, chart data) but its core scoring
    delegates to the same UnifiedAIEngine via ``get_engine()``.

SINGLE entry point for ALL AI intelligence calls across the platform.

Every frontend call (USER/ADMIN/MENTOR) flows through here so we can:
  1. Log every request/response
  2. Track latency & costs
  3. Route to appropriate engine(s) via RoutingPolicy
  4. Apply confidence calibration
  5. Record for ground-truth correlation
  6. Feed metrics to drift detection

Usage:
    from services.ai_engine.control_plane import get_gateway
    
    gateway = get_gateway()
    
    # Score a CV
    result = gateway.score_candidate(text="...", skills=["Python"], ...)
    
    # Extract skills from text
    result = gateway.extract_skills(text="Senior Python developer...")
    
    # Match CV to JD
    result = gateway.match_cv_jd(cv_text="...", jd_text="...")
    
    # Generate CV rewrite
    result = gateway.rewrite_cv(original="...", target_role="...", style="professional")
    
    # Ask a career question (uses LLM)
    result = gateway.career_qa(question="How do I become a data scientist?")
    
    # Get chart data (spider, covery quadrant, etc.)
    result = gateway.get_chart_data(chart_type="spider", user_id="...", context={})
    
    # Generate smart questions for interview prep  
    result = gateway.generate_smart_questions(role="...", company="...", context={})

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from threading import Lock

import numpy as np

logger = logging.getLogger("AIGateway")


# ── Data Classes ─────────────────────────────────────────────────────────

@dataclass
class GatewayRequest:
    """Encapsulates an incoming AI request."""
    request_id: str
    task_type: str  # "score", "extract", "match", "rewrite", "qa", "chart", "questions"
    user_id: Optional[str] = None
    role: str = "user"  # "user", "admin", "mentor"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type,
            "user_id": self.user_id,
            "role": self.role,
            "payload_keys": list(self.payload.keys()),
            "timestamp": self.timestamp,
        }


@dataclass
class GatewayResponse:
    """Encapsulates an AI response with full metadata."""
    request_id: str
    success: bool
    result: Any
    confidence: float = 0.0
    calibrated_confidence: float = 0.0
    engines_used: List[str] = field(default_factory=list)
    routing_decision: str = ""
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result if isinstance(self.result, (dict, list, str, int, float, bool, type(None))) else str(self.result),
            "confidence": round(self.confidence, 4),
            "calibrated_confidence": round(self.calibrated_confidence, 4),
            "engines_used": self.engines_used,
            "routing_decision": self.routing_decision,
            "latency_ms": round(self.latency_ms, 2),
            "cost_estimate": round(self.cost_estimate, 6),
            "warnings": self.warnings,
            "error": self.error,
            "timestamp": self.timestamp,
        }


# ── Gateway Implementation ───────────────────────────────────────────────

class AIGateway:
    """
    Unified AI Gateway — the measurement + control layer for all AI operations.
    
    Integrates:
        - UnifiedAIEngine (6 ML engines)
        - LLM Gateway (OpenAI, Anthropic, etc.)
        - Collocation Engine (terminology)
        - Expert System (rules)
        - Email Intelligence
    
    With Control Plane components:
        - Routing Policy
        - Confidence Calibration
        - Outcome Tracking
        - Drift Detection
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(__file__).parent.parent / "gateway_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = Lock()
        self._request_log: List[Dict] = []
        self._max_log_size = 10000
        
        # Lazy-load engines
        self._unified_engine = None
        self._llm_gateway = None
        self._collocation_engine = None
        self._expert_system = None
        self._routing_policy = None
        self._calibrator = None
        self._outcome_tracker = None
        self._drift_detector = None
        
        # Cost estimates per token (USD)
        self._cost_per_token = {
            "openai": 0.00003,
            "anthropic": 0.00003,
            "local": 0.0,
            "ml_inference": 0.000001,
        }
        
        logger.info("AIGateway initialized (log_dir=%s)", self.log_dir)
    
    # ── Lazy Loaders ─────────────────────────────────────────────────────
    
    @property
    def unified_engine(self):
        if self._unified_engine is None:
            try:
                from services.ai_engine.unified_ai_engine import get_engine
                self._unified_engine = get_engine()
            except Exception as e:
                logger.warning("Failed to load UnifiedAIEngine: %s", e)
        return self._unified_engine
    
    @property
    def llm_gateway(self):
        if self._llm_gateway is None:
            try:
                from services.ai_engine.llm_gateway import llm_gateway
                self._llm_gateway = llm_gateway
            except Exception as e:
                logger.warning("Failed to load LLM Gateway: %s", e)
        return self._llm_gateway
    
    @property
    def collocation_engine(self):
        if self._collocation_engine is None:
            try:
                from services.ai_engine.collocation_engine import CollocationEngine
                self._collocation_engine = CollocationEngine()
            except Exception as e:
                logger.warning("Failed to load CollocationEngine: %s", e)
        return self._collocation_engine
    
    @property
    def expert_system(self):
        if self._expert_system is None:
            try:
                from services.ai_engine.expert_system import career_rules, skill_matcher
                self._expert_system = {"career_rules": career_rules, "skill_matcher": skill_matcher}
            except Exception as e:
                logger.warning("Failed to load ExpertSystem: %s", e)
        return self._expert_system
    
    @property
    def routing_policy(self):
        if self._routing_policy is None:
            try:
                from services.ai_engine.control_plane.routing import get_router
                self._routing_policy = get_router()
            except Exception as e:
                logger.warning("Failed to load RoutingPolicy: %s", e)
        return self._routing_policy
    
    @property
    def calibrator(self):
        if self._calibrator is None:
            try:
                from services.ai_engine.control_plane.calibration import get_calibrator
                self._calibrator = get_calibrator()
            except Exception as e:
                logger.warning("Failed to load ConfidenceCalibrator: %s", e)
        return self._calibrator
    
    @property
    def outcome_tracker(self):
        if self._outcome_tracker is None:
            try:
                from services.ai_engine.control_plane.ground_truth import get_outcome_tracker
                self._outcome_tracker = get_outcome_tracker()
            except Exception as e:
                logger.warning("Failed to load OutcomeTracker: %s", e)
        return self._outcome_tracker
    
    @property
    def drift_detector(self):
        if self._drift_detector is None:
            try:
                from services.ai_engine.control_plane.drift import get_drift_detector
                self._drift_detector = get_drift_detector()
            except Exception as e:
                logger.warning("Failed to load DriftDetector: %s", e)
        return self._drift_detector
    
    # ── Core Request Processing ──────────────────────────────────────────
    
    def _make_request(
        self,
        task_type: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayRequest:
        return GatewayRequest(
            request_id=str(uuid.uuid4()),
            task_type=task_type,
            user_id=user_id,
            role=role,
            payload=payload,
        )
    
    def _log_request(self, req: GatewayRequest, resp: GatewayResponse):
        """Log request/response for analytics and ground-truth correlation."""
        entry = {
            "request": req.to_dict(),
            "response": resp.to_dict(),
        }
        
        with self._lock:
            self._request_log.append(entry)
            
            # Trim if too large
            if len(self._request_log) > self._max_log_size:
                self._request_log = self._request_log[-self._max_log_size // 2:]
        
        # Also write to disk periodically
        if len(self._request_log) % 100 == 0:
            self._flush_logs()
        
        # Feed to drift detector
        if self.drift_detector:
            try:
                self.drift_detector.record_prediction(
                    task_type=req.task_type,
                    confidence=resp.confidence,
                    latency_ms=resp.latency_ms,
                    engines_used=resp.engines_used,
                )
            except Exception as e:
                logger.debug("Drift detector record failed: %s", e)
    
    def _flush_logs(self):
        """Write accumulated logs to disk."""
        try:
            log_file = self.log_dir / f"gateway_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with self._lock:
                logs_to_write = self._request_log.copy()
            
            with open(log_file, "a", encoding="utf-8") as f:
                for entry in logs_to_write:
                    f.write(json.dumps(entry) + "\n")
            
            logger.debug("Flushed %d log entries to %s", len(logs_to_write), log_file)
        except Exception as e:
            logger.warning("Failed to flush logs: %s", e)
    
    def _estimate_cost(self, task_type: str, token_count: int = 0, engines_used: List[str] = None) -> float:
        """Estimate cost of the operation."""
        cost = 0.0
        
        if task_type in ("qa", "rewrite"):
            # LLM-heavy tasks
            cost += token_count * self._cost_per_token.get("anthropic", 0.00003)
        elif task_type in ("score", "extract", "match"):
            # ML inference
            cost += self._cost_per_token["ml_inference"] * (len(engines_used) if engines_used else 1)
        
        return cost
    
    # ── Public API: Scoring ──────────────────────────────────────────────
    
    def score_candidate(
        self,
        text: str,
        skills: Optional[List[str]] = None,
        experience_years: int = 0,
        education_level: str = "unknown",
        job_title: str = "",
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Score a candidate CV/profile.
        
        This is the primary scoring endpoint used by:
            - User dashboard (personal score)
            - Admin analytics (batch scoring)
            - Mentor evaluation (mentee assessment)
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="score",
            payload={
                "text_length": len(text),
                "skills_count": len(skills) if skills else 0,
                "experience_years": experience_years,
                "education_level": education_level,
                "job_title": job_title,
            },
            user_id=user_id,
            role=role,
        )
        
        try:
            # Route the request
            routing = "all_engines"
            if self.routing_policy:
                routing = self.routing_policy.decide("score", {
                    "text_length": len(text),
                    "experience_years": experience_years,
                })
            
            # Execute scoring
            if self.unified_engine is None:
                return GatewayResponse(
                    request_id=req.request_id,
                    success=False,
                    result=None,
                    error="UnifiedAIEngine not available",
                )
            
            result = self.unified_engine.score_candidate(
                text=text,
                skills=skills or [],
                experience_years=experience_years,
                education=education_level,
                job_title=job_title,
            )
            
            # Extract confidence & apply calibration
            raw_confidence = result.confidence if hasattr(result, "confidence") else 0.5
            calibrated = raw_confidence
            if self.calibrator:
                calibrated = self.calibrator.calibrate(raw_confidence, task_type="score")
            
            engines_used = list(result.engine_results.keys()) if hasattr(result, "engine_results") else []
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result=result.to_dict() if hasattr(result, "to_dict") else result,
                confidence=raw_confidence,
                calibrated_confidence=calibrated,
                engines_used=engines_used,
                routing_decision=routing,
                latency_ms=latency,
                cost_estimate=self._estimate_cost("score", engines_used=engines_used),
            )
            
            # Log for ground-truth and drift
            self._log_request(req, resp)
            
            return resp
            
        except Exception as e:
            logger.exception("score_candidate failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: Skill Extraction ─────────────────────────────────────
    
    def extract_skills(
        self,
        text: str,
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Extract skills from text (CV, JD, or freeform).
        
        Used by:
            - CV parser (automated skill tagging)
            - JD analyzer (required skills)
            - User profile builder
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="extract",
            payload={"text_length": len(text)},
            user_id=user_id,
            role=role,
        )
        
        try:
            skills = []
            confidence = 0.0
            
            # Use collocation engine for terminology extraction
            if self.collocation_engine:
                matches = self.collocation_engine.match_text(text)
                skills = [m["term"] for m in matches if m.get("type") == "skill"]
                confidence = np.mean([m.get("score", 0.5) for m in matches]) if matches else 0.3
            
            # Augment with expert system patterns if available
            if self.expert_system:
                try:
                    sm = self.expert_system.get("skill_matcher")
                    if sm and hasattr(sm, "extract_skills"):
                        extra = sm.extract_skills(text)
                        skills = list(set(skills + extra))
                except Exception:
                    pass
            
            calibrated = confidence
            if self.calibrator:
                calibrated = self.calibrator.calibrate(confidence, task_type="extract")
            
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result={"skills": skills, "count": len(skills)},
                confidence=confidence,
                calibrated_confidence=calibrated,
                engines_used=["collocation", "expert_system"],
                routing_decision="collocation_first",
                latency_ms=latency,
                cost_estimate=self._estimate_cost("extract"),
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("extract_skills failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: CV-JD Matching ───────────────────────────────────────
    
    def match_cv_jd(
        self,
        cv_text: str,
        jd_text: str,
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Match a CV against a job description.
        
        Used by:
            - Job matching recommendations
            - Application strength prediction
            - ATS pass likelihood
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="match",
            payload={"cv_length": len(cv_text), "jd_length": len(jd_text)},
            user_id=user_id,
            role=role,
        )
        
        try:
            # Extract skills from both
            cv_skills_resp = self.extract_skills(cv_text)
            jd_skills_resp = self.extract_skills(jd_text)
            
            cv_skills = set(cv_skills_resp.result.get("skills", []) if cv_skills_resp.success else [])
            jd_skills = set(jd_skills_resp.result.get("skills", []) if jd_skills_resp.success else [])
            
            # Compute match metrics
            if jd_skills:
                coverage = len(cv_skills & jd_skills) / len(jd_skills)
            else:
                coverage = 0.0
            
            missing = list(jd_skills - cv_skills)
            extra = list(cv_skills - jd_skills)
            
            # Use expert system for detailed matching
            match_score = coverage
            grade = "Unknown"
            
            if self.expert_system:
                try:
                    sm = self.expert_system.get("skill_matcher")
                    if sm:
                        result = sm.score(
                            user_skills=list(cv_skills),
                            role_requirements=list(jd_skills),
                        )
                        match_score = result.get("overall_score", coverage)
                        grade = result.get("grade", "Unknown")
                except Exception:
                    pass
            
            confidence = min(0.95, 0.3 + coverage * 0.6)
            calibrated = confidence
            if self.calibrator:
                calibrated = self.calibrator.calibrate(confidence, task_type="match")
            
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result={
                    "match_score": round(match_score * 100, 2),
                    "coverage": round(coverage * 100, 2),
                    "grade": grade,
                    "cv_skills": list(cv_skills),
                    "jd_skills": list(jd_skills),
                    "missing_skills": missing[:20],  # Top 20
                    "extra_skills": extra[:20],
                },
                confidence=confidence,
                calibrated_confidence=calibrated,
                engines_used=["collocation", "expert_system"],
                routing_decision="skill_matching",
                latency_ms=latency,
                cost_estimate=self._estimate_cost("match"),
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("match_cv_jd failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: CV Rewrite ───────────────────────────────────────────
    
    def rewrite_cv(
        self,
        original_text: str,
        target_role: str = "",
        style: str = "professional",
        focus_areas: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Generate a CV rewrite suggestion.
        
        Uses LLM for generation, constrained by expert rules.
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="rewrite",
            payload={
                "original_length": len(original_text),
                "target_role": target_role,
                "style": style,
                "focus_areas": focus_areas or [],
            },
            user_id=user_id,
            role=role,
        )
        
        try:
            if self.llm_gateway is None:
                return GatewayResponse(
                    request_id=req.request_id,
                    success=False,
                    result=None,
                    error="LLM Gateway not available",
                )
            
            # Build prompt with constraints
            focus_str = ", ".join(focus_areas) if focus_areas else "overall improvement"
            
            prompt = f"""You are a professional CV writer. Rewrite the following CV section to be more impactful.

Target Role: {target_role or 'General professional role'}
Style: {style}
Focus Areas: {focus_str}

Original Text:
{original_text[:3000]}

Instructions:
1. Maintain factual accuracy - do not invent experiences
2. Use strong action verbs
3. Quantify achievements where possible
4. Optimize for ATS keyword matching
5. Keep professional tone

Rewritten Version:"""

            response = self.llm_gateway.generate(prompt, max_tokens=1500)
            
            if not response.success:
                return GatewayResponse(
                    request_id=req.request_id,
                    success=False,
                    result=None,
                    error=response.error,
                )
            
            token_count = response.usage.get("total_tokens", 500)
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result={
                    "rewritten_text": response.text,
                    "provider": response.provider,
                    "model": response.model,
                },
                confidence=0.8,  # LLM outputs have fixed confidence
                calibrated_confidence=0.75,
                engines_used=[response.provider],
                routing_decision="llm_direct",
                latency_ms=latency,
                cost_estimate=self._estimate_cost("rewrite", token_count=token_count),
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("rewrite_cv failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: Career Q&A ───────────────────────────────────────────
    
    def career_qa(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Answer career-related questions using LLM + RAG.
        
        Uses expert system rules to constrain answers.
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="qa",
            payload={"question_length": len(question), "has_context": context is not None},
            user_id=user_id,
            role=role,
        )
        
        try:
            if self.llm_gateway is None:
                return GatewayResponse(
                    request_id=req.request_id,
                    success=False,
                    result=None,
                    error="LLM Gateway not available",
                )
            
            # Build context from career rules if available
            context_str = ""
            if context:
                context_str = json.dumps(context, indent=2)[:1000]
            
            prompt = f"""You are a career advisor. Answer the following question thoughtfully.

Question: {question}

{"Context: " + context_str if context_str else ""}

Provide practical, actionable advice. Be encouraging but realistic."""

            response = self.llm_gateway.generate(prompt, max_tokens=1000)
            
            if not response.success:
                return GatewayResponse(
                    request_id=req.request_id,
                    success=False,
                    result=None,
                    error=response.error,
                )
            
            token_count = response.usage.get("total_tokens", 300)
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result={
                    "answer": response.text,
                    "provider": response.provider,
                    "model": response.model,
                },
                confidence=0.75,
                calibrated_confidence=0.7,
                engines_used=[response.provider],
                routing_decision="llm_qa",
                latency_ms=latency,
                cost_estimate=self._estimate_cost("qa", token_count=token_count),
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("career_qa failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: Chart Data ───────────────────────────────────────────
    
    def get_chart_data(
        self,
        chart_type: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Generate data for visualizations.
        
        Chart types:
            - spider: Multi-dimensional skill radar
            - covery_quadrant: Career trajectory mapping
            - skill_gap: Missing skills analysis
            - industry_distribution: Industry fit breakdown
            - timeline: Career progression timeline
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="chart",
            payload={"chart_type": chart_type, "has_context": context is not None},
            user_id=user_id,
            role=role,
        )
        
        try:
            context = context or {}
            chart_data = {}
            
            if chart_type == "spider":
                # Multi-dimensional skill radar
                # Pull dimension scores from unified engine
                if self.unified_engine and "text" in context:
                    score_result = self.score_candidate(
                        text=context.get("text", ""),
                        skills=context.get("skills", []),
                        experience_years=context.get("experience_years", 0),
                        education_level=context.get("education_level", "unknown"),
                        user_id=user_id,
                        role=role,
                    )
                    if score_result.success and isinstance(score_result.result, dict):
                        dims = score_result.result.get("dimension_scores", {})
                        chart_data = {
                            "labels": list(dims.keys()),
                            "values": list(dims.values()),
                            "max_value": 100,
                        }
                    else:
                        chart_data = {"labels": [], "values": [], "max_value": 100}
                else:
                    # Default empty spider
                    chart_data = {
                        "labels": ["Technical", "Experience", "Education", "Communication", "Leadership"],
                        "values": [0, 0, 0, 0, 0],
                        "max_value": 100,
                    }
            
            elif chart_type == "covery_quadrant":
                # Career trajectory: Growth Potential vs Current Performance
                chart_data = {
                    "x_axis": "Current Performance",
                    "y_axis": "Growth Potential", 
                    "quadrants": [
                        {"name": "Star", "description": "High performance, high potential"},
                        {"name": "Workhorse", "description": "High performance, lower potential"},
                        {"name": "Rising Star", "description": "Lower performance, high potential"},
                        {"name": "Developing", "description": "Needs development in both areas"},
                    ],
                    "position": context.get("position", {"x": 50, "y": 50}),
                }
            
            elif chart_type == "skill_gap":
                # Missing skills analysis
                if "cv_text" in context and "jd_text" in context:
                    match_result = self.match_cv_jd(
                        cv_text=context["cv_text"],
                        jd_text=context["jd_text"],
                        user_id=user_id,
                        role=role,
                    )
                    if match_result.success:
                        chart_data = {
                            "coverage": match_result.result.get("coverage", 0),
                            "missing_skills": match_result.result.get("missing_skills", []),
                            "matched_skills": match_result.result.get("cv_skills", []),
                        }
                else:
                    chart_data = {"coverage": 0, "missing_skills": [], "matched_skills": []}
            
            elif chart_type == "industry_distribution":
                # Industry fit breakdown from engines
                if self.unified_engine and "text" in context:
                    score_result = self.score_candidate(
                        text=context.get("text", ""),
                        user_id=user_id,
                        role=role,
                    )
                    if score_result.success and isinstance(score_result.result, dict):
                        chart_data = {
                            "predicted_industry": score_result.result.get("predicted_industry", "Unknown"),
                            "confidence": score_result.result.get("confidence", 0),
                            "engine_breakdown": score_result.result.get("engine_breakdown", {}),
                        }
                else:
                    chart_data = {"predicted_industry": "Unknown", "confidence": 0}
            
            elif chart_type == "timeline":
                # Career progression timeline
                chart_data = {
                    "events": context.get("events", []),
                    "milestones": context.get("milestones", []),
                }
            
            else:
                chart_data = {"error": f"Unknown chart type: {chart_type}"}
            
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result=chart_data,
                confidence=0.85,
                calibrated_confidence=0.8,
                engines_used=["unified" if chart_type in ("spider", "industry_distribution") else "rule_based"],
                routing_decision=f"chart_{chart_type}",
                latency_ms=latency,
                cost_estimate=0.0,
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("get_chart_data failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Public API: Smart Questions ──────────────────────────────────────
    
    def generate_smart_questions(
        self,
        target_role: str,
        company: str = "",
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        role: str = "user",
    ) -> GatewayResponse:
        """
        Generate intelligent interview preparation questions.
        
        Combines:
            - Role-specific questions from expert system
            - Company-specific insights if available
            - LLM-generated situational questions
        """
        start = time.perf_counter()
        
        req = self._make_request(
            task_type="questions",
            payload={"target_role": target_role, "company": company},
            user_id=user_id,
            role=role,
        )
        
        try:
            questions = []
            sections = {}
            
            # Get role-specific questions from expert system
            if self.expert_system:
                try:
                    cr = self.expert_system.get("career_rules")
                    if cr and hasattr(cr, "get_interview_questions"):
                        rule_questions = cr.get_interview_questions(target_role)
                        sections["behavioral"] = rule_questions[:5]
                except Exception:
                    pass
            
            # Generate situational questions via LLM if available
            if self.llm_gateway:
                try:
                    prompt = f"""Generate 5 interview questions for a {target_role} position{' at ' + company if company else ''}.

Include:
1. One technical question
2. One behavioral question
3. One situational question
4. One question about career goals
5. One question to ask the interviewer

Format as a JSON array of objects with "category" and "question" keys."""

                    response = self.llm_gateway.generate(prompt, max_tokens=800)
                    if response.success:
                        try:
                            # Parse JSON from response
                            import re
                            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                            if json_match:
                                llm_questions = json.loads(json_match.group())
                                sections["situational"] = llm_questions
                        except Exception:
                            # Fallback: treat as plain text
                            sections["llm_generated"] = [{"question": response.text}]
                except Exception:
                    pass
            
            # Compile all questions
            for category, qs in sections.items():
                for q in qs:
                    if isinstance(q, dict):
                        questions.append({**q, "source": category})
                    else:
                        questions.append({"question": str(q), "source": category})
            
            latency = (time.perf_counter() - start) * 1000
            
            resp = GatewayResponse(
                request_id=req.request_id,
                success=True,
                result={
                    "questions": questions,
                    "role": target_role,
                    "company": company,
                    "sections": list(sections.keys()),
                },
                confidence=0.8,
                calibrated_confidence=0.75,
                engines_used=["expert_system", "llm"] if self.llm_gateway else ["expert_system"],
                routing_decision="questions_hybrid",
                latency_ms=latency,
                cost_estimate=self._estimate_cost("questions", token_count=400),
            )
            
            self._log_request(req, resp)
            return resp
            
        except Exception as e:
            logger.exception("generate_smart_questions failed")
            return GatewayResponse(
                request_id=req.request_id,
                success=False,
                result=None,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    # ── Outcome Recording (Ground-Truth Loop) ────────────────────────────
    
    def record_outcome(
        self,
        request_id: str,
        outcome_type: str,
        outcome_value: Any,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Record an outcome signal for ground-truth correlation.
        
        Outcome types:
            - interview_requested: User got an interview
            - offer_received: Job offer received
            - recommendation_accepted: User accepted AI recommendation
            - rewrite_adopted: User used rewritten text
            - question_helpful: User rated question as helpful
            - match_applied: User applied to matched job
        """
        if self.outcome_tracker is None:
            logger.warning("OutcomeTracker not available")
            return False
        
        try:
            return self.outcome_tracker.record(
                request_id=request_id,
                outcome_type=outcome_type,
                outcome_value=outcome_value,
                user_id=user_id,
            )
        except Exception as e:
            logger.exception("record_outcome failed")
            return False
    
    # ── Analytics ────────────────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        with self._lock:
            total = len(self._request_log)
            
        task_counts: Dict[str, int] = {}
        latencies: List[float] = []
        
        with self._lock:
            for entry in self._request_log[-1000:]:
                req = entry.get("request", {})
                resp = entry.get("response", {})
                
                task = req.get("task_type", "unknown")
                task_counts[task] = task_counts.get(task, 0) + 1
                
                latencies.append(resp.get("latency_ms", 0))
        
        return {
            "total_requests": total,
            "task_distribution": task_counts,
            "avg_latency_ms": round(np.mean(latencies), 2) if latencies else 0,
            "p95_latency_ms": round(np.percentile(latencies, 95), 2) if latencies else 0,
            "engines_available": {
                "unified": self._unified_engine is not None,
                "llm": self._llm_gateway is not None,
                "collocation": self._collocation_engine is not None,
                "expert": self._expert_system is not None,
            },
        }


# ── Module-level Singleton ───────────────────────────────────────────────

_gateway_instance: Optional[AIGateway] = None
_gateway_lock = Lock()


def get_gateway() -> AIGateway:
    """Get the module-level AIGateway singleton."""
    global _gateway_instance
    
    with _gateway_lock:
        if _gateway_instance is None:
            _gateway_instance = AIGateway()
        return _gateway_instance
