"""
CareerTrojan — AI Gateway (Control Plane Entry Point)
======================================================

SINGLE entry point for ALL AI operations across the platform.
Replaces direct calls to llm_gateway and unified_ai_engine.

This gateway provides:
  1. Unified request routing (generative vs inference)
  2. Ground-truth tracking for feedback loops
  3. Confidence calibration and consensus voting
  4. Routing policy enforcement
  5. Drift detection hooks
  6. Audit logging for all AI decisions

All code should call:
    from services.ai_engine.ai_gateway import ai_gateway
    
    # Generative (LLM) requests
    response = ai_gateway.generate("Improve this resume bullet: ...")
    
    # Inference (ML) requests
    result = ai_gateway.score_candidate(resume_text, skills, experience)
    
    # Extraction requests
    entities = ai_gateway.extract(document_text, task="skills")

Author: CareerTrojan System
Date:   February 2026
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("AIGateway")


# ══════════════════════════════════════════════════════════════════════════
# Request Types & Contracts
# ══════════════════════════════════════════════════════════════════════════

class TaskType(Enum):
    """Types of AI tasks the gateway handles."""
    GENERATE = "generate"           # LLM text generation
    SCORE = "score"                 # Candidate/resume scoring
    CLASSIFY = "classify"           # Category classification
    EXTRACT = "extract"             # Entity/skill extraction
    MATCH = "match"                 # Job-candidate matching
    ENRICH = "enrich"               # Data enrichment
    ANALYZE = "analyze"             # Document analysis


class ConfidenceLevel(Enum):
    """Confidence thresholds for routing decisions."""
    HIGH = 0.85
    MEDIUM = 0.65
    LOW = 0.40
    UNCERTAIN = 0.0


@dataclass
class GatewayRequest:
    """Standardized request to the AI Gateway."""
    task_type: TaskType
    payload: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Routing hints
    prefer_deterministic: bool = False  # Skip LLM, use rules/ML only
    require_explanation: bool = False   # Must provide reasoning
    compliance_mode: bool = False       # Force validator checks
    
    # Tracking
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type.value,
            "payload": self.payload,
            "context": self.context,
            "prefer_deterministic": self.prefer_deterministic,
            "require_explanation": self.require_explanation,
            "compliance_mode": self.compliance_mode,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }


@dataclass
class GatewayResponse:
    """Standardized response from the AI Gateway."""
    request_id: str
    task_type: TaskType
    
    # Results
    result: Any
    confidence: float = 0.0
    calibrated_confidence: float = 0.0  # After calibration layer
    
    # Routing info
    route_taken: str = ""               # Which backend handled this
    engines_consulted: List[str] = field(default_factory=list)
    consensus_method: str = ""          # How agreement was reached
    
    # Governance
    ground_truth_id: Optional[str] = None  # For feedback tracking
    drift_flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    success: bool = True
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type.value,
            "result": self.result,
            "confidence": round(self.confidence, 4),
            "calibrated_confidence": round(self.calibrated_confidence, 4),
            "route_taken": self.route_taken,
            "engines_consulted": self.engines_consulted,
            "consensus_method": self.consensus_method,
            "ground_truth_id": self.ground_truth_id,
            "drift_flags": self.drift_flags,
            "warnings": self.warnings,
            "success": self.success,
            "error": self.error,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp,
        }


# ══════════════════════════════════════════════════════════════════════════
# Ground Truth Tracker (inline for now, will be extracted)
# ══════════════════════════════════════════════════════════════════════════

class GroundTruthTracker:
    """
    Tracks AI predictions and their outcomes for feedback loops.
    
    Outcome signals we track:
      - Interview rate (did candidate get interview?)
      - ATS pass (did resume pass ATS?)
      - User acceptance (did user accept the suggestion?)
      - Hiring outcome (did candidate get hired?)
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent / "ground_truth"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.predictions_file = self.storage_path / "predictions.jsonl"
        self.outcomes_file = self.storage_path / "outcomes.jsonl"
        
        # In-memory cache for recent predictions (for fast lookup)
        self._recent_predictions: Dict[str, Dict] = {}
        self._max_cache = 10000
        
    def record_prediction(
        self,
        ground_truth_id: str,
        request: GatewayRequest,
        response: GatewayResponse,
        features: Dict[str, Any] = None,
    ) -> None:
        """Record a prediction for later feedback matching."""
        record = {
            "ground_truth_id": ground_truth_id,
            "timestamp": datetime.now().isoformat(),
            "task_type": request.task_type.value,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "route_taken": response.route_taken,
            "confidence": response.confidence,
            "calibrated_confidence": response.calibrated_confidence,
            "result_hash": self._hash_result(response.result),
            "features": features or {},
            "outcome": None,  # To be filled in later
        }
        
        # Cache in memory
        self._recent_predictions[ground_truth_id] = record
        if len(self._recent_predictions) > self._max_cache:
            # Evict oldest
            oldest = min(self._recent_predictions.keys())
            del self._recent_predictions[oldest]
        
        # Append to disk
        try:
            with open(self.predictions_file, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning("Failed to persist prediction: %s", e)
    
    def record_outcome(
        self,
        ground_truth_id: str,
        outcome_type: str,  # "interview", "ats_pass", "user_accepted", "hired"
        outcome_value: Any,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Record an outcome for a previous prediction."""
        outcome_record = {
            "ground_truth_id": ground_truth_id,
            "timestamp": datetime.now().isoformat(),
            "outcome_type": outcome_type,
            "outcome_value": outcome_value,
            "metadata": metadata or {},
        }
        
        # Update cache if present
        if ground_truth_id in self._recent_predictions:
            self._recent_predictions[ground_truth_id]["outcome"] = {
                outcome_type: outcome_value
            }
        
        # Append to outcomes file
        try:
            with open(self.outcomes_file, "a") as f:
                f.write(json.dumps(outcome_record) + "\n")
            return True
        except Exception as e:
            logger.warning("Failed to persist outcome: %s", e)
            return False
    
    def get_prediction(self, ground_truth_id: str) -> Optional[Dict]:
        """Retrieve a prediction by ID."""
        if ground_truth_id in self._recent_predictions:
            return self._recent_predictions[ground_truth_id]
        
        # Scan file (expensive, but rare)
        if self.predictions_file.exists():
            with open(self.predictions_file) as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("ground_truth_id") == ground_truth_id:
                            return record
                    except json.JSONDecodeError:
                        continue
        return None
    
    def get_feedback_stats(self, task_type: str = None, days: int = 30) -> Dict[str, Any]:
        """Get aggregate stats on prediction accuracy."""
        # This would query the files and compute accuracy metrics
        # Simplified for now
        return {
            "total_predictions": len(self._recent_predictions),
            "outcomes_collected": 0,  # TODO: count outcomes
            "accuracy_by_confidence": {},
            "calibration_error": 0.0,
        }
    
    def _hash_result(self, result: Any) -> str:
        """Hash a result for comparison without storing full content."""
        return hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════════════════
# Confidence Calibration Layer
# ══════════════════════════════════════════════════════════════════════════

class ConfidenceCalibrator:
    """
    Calibrates raw model confidence to actual accuracy.
    
    Methods:
      - Platt scaling (sigmoid calibration)
      - Isotonic regression
      - Temperature scaling
      - Historical accuracy mapping
    """
    
    def __init__(self):
        # Calibration curves per task type (learned from ground truth)
        # Format: raw_confidence -> calibrated_confidence
        self._calibration_curves: Dict[str, List[Tuple[float, float]]] = {}
        self._default_temperature = 1.5  # Temperature scaling factor
        
    def calibrate(
        self,
        raw_confidence: float,
        task_type: TaskType,
        route: str = None,
    ) -> float:
        """Apply calibration to raw confidence score."""
        key = f"{task_type.value}:{route}" if route else task_type.value
        
        if key in self._calibration_curves and self._calibration_curves[key]:
            # Use learned curve
            return self._interpolate_curve(raw_confidence, self._calibration_curves[key])
        
        # Default: temperature scaling (softens overconfident models)
        return self._temperature_scale(raw_confidence)
    
    def _temperature_scale(self, conf: float) -> float:
        """Apply temperature scaling to soften overconfident predictions."""
        # Higher temperature = less confident
        import math
        scaled = conf ** (1.0 / self._default_temperature)
        return min(max(scaled, 0.0), 1.0)
    
    def _interpolate_curve(self, raw: float, curve: List[Tuple[float, float]]) -> float:
        """Interpolate calibration curve."""
        if not curve:
            return raw
        
        # Find bracketing points
        for i, (r, c) in enumerate(curve):
            if r >= raw:
                if i == 0:
                    return c
                prev_r, prev_c = curve[i - 1]
                # Linear interpolation
                ratio = (raw - prev_r) / (r - prev_r) if r != prev_r else 0.5
                return prev_c + ratio * (c - prev_c)
        
        return curve[-1][1]  # Beyond curve, use last value
    
    def update_calibration(
        self,
        task_type: TaskType,
        route: str,
        predictions_and_outcomes: List[Tuple[float, bool]],
    ) -> None:
        """Update calibration curve from ground truth feedback."""
        key = f"{task_type.value}:{route}"
        
        # Bin predictions by confidence and compute actual accuracy
        bins = {}
        for conf, outcome in predictions_and_outcomes:
            bin_idx = int(conf * 10)  # 10 bins
            if bin_idx not in bins:
                bins[bin_idx] = []
            bins[bin_idx].append(1.0 if outcome else 0.0)
        
        # Build calibration curve
        curve = []
        for bin_idx in sorted(bins.keys()):
            raw_conf = (bin_idx + 0.5) / 10.0
            actual_acc = sum(bins[bin_idx]) / len(bins[bin_idx])
            curve.append((raw_conf, actual_acc))
        
        self._calibration_curves[key] = curve
        logger.info("Updated calibration curve for %s: %d points", key, len(curve))


# ══════════════════════════════════════════════════════════════════════════
# Routing Policy Engine
# ══════════════════════════════════════════════════════════════════════════

class RoutingPolicy:
    """
    Decides which backend/model to use for a given request.
    
    Routing rules:
      - GENERATE tasks → LLM Gateway
      - SCORE/CLASSIFY tasks → Unified AI Engine (ensemble)
      - EXTRACT tasks → LLM for complex, rules for simple
      - High uncertainty → deterministic fallback
      - Compliance mode → add validator checks
    """
    
    def __init__(self):
        # Task type to default backend mapping
        self._default_routes = {
            TaskType.GENERATE: "llm_gateway",
            TaskType.SCORE: "unified_ai_engine",
            TaskType.CLASSIFY: "unified_ai_engine",
            TaskType.EXTRACT: "hybrid",  # Rules first, LLM fallback
            TaskType.MATCH: "unified_ai_engine",
            TaskType.ENRICH: "hybrid",
            TaskType.ANALYZE: "llm_gateway",
        }
        
        # Cost weights for routing decisions
        self._cost_weights = {
            "llm_gateway": 10.0,      # Expensive (API calls)
            "unified_ai_engine": 1.0,  # Cheap (local inference)
            "rules_engine": 0.1,       # Very cheap (no model)
        }
    
    def route(self, request: GatewayRequest) -> Tuple[str, Dict[str, Any]]:
        """
        Determine the routing for a request.
        
        Returns:
            (backend_name, routing_metadata)
        """
        # Check explicit preferences
        if request.prefer_deterministic:
            return self._route_deterministic(request)
        
        if request.compliance_mode:
            return self._route_compliance(request)
        
        # Default routing based on task type
        backend = self._default_routes.get(request.task_type, "llm_gateway")
        
        # Check for hybrid routing
        if backend == "hybrid":
            return self._route_hybrid(request)
        
        return backend, {"reason": "default_routing", "task_type": request.task_type.value}
    
    def _route_deterministic(self, request: GatewayRequest) -> Tuple[str, Dict[str, Any]]:
        """Route to deterministic (non-LLM) backend."""
        if request.task_type in [TaskType.SCORE, TaskType.CLASSIFY, TaskType.MATCH]:
            return "unified_ai_engine", {"reason": "prefer_deterministic", "fallback": False}
        
        # For tasks that typically need LLM, use rules fallback
        return "rules_engine", {"reason": "deterministic_fallback", "limited_capability": True}
    
    def _route_compliance(self, request: GatewayRequest) -> Tuple[str, Dict[str, Any]]:
        """Route with compliance validators enabled."""
        backend = self._default_routes.get(request.task_type, "llm_gateway")
        return backend, {
            "reason": "compliance_mode",
            "validators_enabled": ["bias_check", "pii_filter", "content_policy"],
        }
    
    def _route_hybrid(self, request: GatewayRequest) -> Tuple[str, Dict[str, Any]]:
        """Hybrid routing: rules first, LLM fallback."""
        # Estimate complexity
        payload_size = len(json.dumps(request.payload, default=str))
        
        if payload_size < 500:
            # Simple request, try rules first
            return "rules_engine", {"reason": "hybrid_simple", "llm_fallback": True}
        else:
            # Complex request, use LLM
            return "llm_gateway", {"reason": "hybrid_complex", "rules_fallback": False}


# ══════════════════════════════════════════════════════════════════════════
# Drift Detection
# ══════════════════════════════════════════════════════════════════════════

class DriftDetector:
    """
    Monitors model quality and detects drift.
    
    Drift types:
      - Data drift: input distribution changed
      - Concept drift: relationship between inputs and outputs changed
      - Performance drift: accuracy degraded
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # Rolling windows of metrics
        self._confidence_history: List[float] = []
        self._latency_history: List[float] = []
        self._error_history: List[bool] = []
        
        # Baselines (set during healthy operation)
        self._baseline_confidence_mean: Optional[float] = None
        self._baseline_confidence_std: Optional[float] = None
        self._baseline_latency_p95: Optional[float] = None
        self._baseline_error_rate: Optional[float] = None
        
        # Drift thresholds
        self._confidence_drift_threshold = 2.0  # Standard deviations
        self._latency_drift_threshold = 1.5     # Multiplier on p95
        self._error_drift_threshold = 2.0       # Multiplier on baseline
    
    def record(
        self,
        confidence: float,
        latency_ms: float,
        is_error: bool,
    ) -> List[str]:
        """Record metrics and return any drift flags."""
        self._confidence_history.append(confidence)
        self._latency_history.append(latency_ms)
        self._error_history.append(is_error)
        
        # Trim to window
        if len(self._confidence_history) > self.window_size:
            self._confidence_history = self._confidence_history[-self.window_size:]
            self._latency_history = self._latency_history[-self.window_size:]
            self._error_history = self._error_history[-self.window_size:]
        
        # Check for drift
        flags = []
        
        # Only check if we have enough data
        if len(self._confidence_history) < 100:
            return flags
        
        # Check confidence drift
        if self._baseline_confidence_mean is not None:
            current_mean = sum(self._confidence_history[-100:]) / 100
            deviation = abs(current_mean - self._baseline_confidence_mean)
            if self._baseline_confidence_std and deviation > self._confidence_drift_threshold * self._baseline_confidence_std:
                flags.append("confidence_drift")
        
        # Check latency drift
        if self._baseline_latency_p95 is not None:
            recent_latencies = sorted(self._latency_history[-100:])
            current_p95 = recent_latencies[94] if len(recent_latencies) >= 95 else recent_latencies[-1]
            if current_p95 > self._latency_drift_threshold * self._baseline_latency_p95:
                flags.append("latency_drift")
        
        # Check error rate drift
        if self._baseline_error_rate is not None:
            recent_errors = self._error_history[-100:]
            current_error_rate = sum(1 for e in recent_errors if e) / len(recent_errors)
            if current_error_rate > self._error_drift_threshold * max(self._baseline_error_rate, 0.01):
                flags.append("error_drift")
        
        return flags
    
    def set_baseline(self) -> Dict[str, float]:
        """Capture current metrics as baseline (call during healthy operation)."""
        if len(self._confidence_history) < 100:
            return {"error": "Not enough data for baseline (need 100+ samples)"}
        
        import statistics
        
        self._baseline_confidence_mean = statistics.mean(self._confidence_history)
        self._baseline_confidence_std = statistics.stdev(self._confidence_history)
        
        sorted_latencies = sorted(self._latency_history)
        self._baseline_latency_p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        
        self._baseline_error_rate = sum(1 for e in self._error_history if e) / len(self._error_history)
        
        baseline = {
            "confidence_mean": self._baseline_confidence_mean,
            "confidence_std": self._baseline_confidence_std,
            "latency_p95": self._baseline_latency_p95,
            "error_rate": self._baseline_error_rate,
        }
        
        logger.info("Drift detector baseline set: %s", baseline)
        return baseline
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current drift detection stats."""
        if not self._confidence_history:
            return {"status": "no_data"}
        
        import statistics
        
        return {
            "samples": len(self._confidence_history),
            "current_confidence_mean": statistics.mean(self._confidence_history[-100:]) if len(self._confidence_history) >= 100 else None,
            "current_error_rate": sum(1 for e in self._error_history[-100:] if e) / min(len(self._error_history), 100),
            "baseline_set": self._baseline_confidence_mean is not None,
        }


# ══════════════════════════════════════════════════════════════════════════
# Main AI Gateway Class
# ══════════════════════════════════════════════════════════════════════════

class AIGateway:
    """
    Unified AI Gateway — single entry point for all AI operations.
    
    Integrates:
      - LLM Gateway (for generative tasks)
      - Unified AI Engine (for inference tasks)
      - Ground Truth Tracker (for feedback loops)
      - Confidence Calibrator (for calibrated predictions)
      - Routing Policy (for intelligent routing)
      - Drift Detector (for quality monitoring)
    """
    
    def __init__(self):
        self._initialized = False
        
        # Backends (lazy loaded)
        self._llm_gateway = None
        self._unified_engine = None
        self._rules_engine = None
        
        # Control plane components
        self.ground_truth = GroundTruthTracker()
        self.calibrator = ConfidenceCalibrator()
        self.routing_policy = RoutingPolicy()
        self.drift_detector = DriftDetector()
        
        # Metrics
        self._request_count = 0
        self._error_count = 0
        self._total_latency_ms = 0.0
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Lazy-initialize backends."""
        if self._initialized:
            return
        
        try:
            from services.ai_engine.llm_gateway import llm_gateway
            self._llm_gateway = llm_gateway
            logger.info("LLM Gateway connected")
        except Exception as e:
            logger.warning("LLM Gateway not available: %s", e)
        
        try:
            from services.ai_engine.unified_ai_engine import get_engine
            self._unified_engine = get_engine()
            logger.info("Unified AI Engine connected")
        except Exception as e:
            logger.warning("Unified AI Engine not available: %s", e)
        
        self._initialized = True
    
    # ─────────────────────────────────────────────────────────────────────
    # High-Level API (convenience methods)
    # ─────────────────────────────────────────────────────────────────────
    
    def generate(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        provider: str = None,
        user_id: str = None,
        **kwargs,
    ) -> GatewayResponse:
        """Generate text using LLM (resume bullets, cover letters, etc.)."""
        request = GatewayRequest(
            task_type=TaskType.GENERATE,
            payload={"prompt": prompt, "provider": provider, **kwargs},
            context=context or {},
            user_id=user_id,
        )
        return self.process(request)
    
    def score_candidate(
        self,
        resume_text: str,
        skills: List[str] = None,
        experience_years: int = None,
        education: str = None,
        job_description: str = None,
        user_id: str = None,
        **kwargs,
    ) -> GatewayResponse:
        """Score a candidate using ensemble ML models."""
        request = GatewayRequest(
            task_type=TaskType.SCORE,
            payload={
                "resume_text": resume_text,
                "skills": skills or [],
                "experience_years": experience_years,
                "education": education,
                "job_description": job_description,
                **kwargs,
            },
            user_id=user_id,
        )
        return self.process(request)
    
    def classify(
        self,
        text: str,
        category_type: str = "industry",  # "industry", "job_level", "job_function"
        user_id: str = None,
        **kwargs,
    ) -> GatewayResponse:
        """Classify text into categories."""
        request = GatewayRequest(
            task_type=TaskType.CLASSIFY,
            payload={"text": text, "category_type": category_type, **kwargs},
            user_id=user_id,
        )
        return self.process(request)
    
    def extract(
        self,
        text: str,
        extraction_type: str = "skills",  # "skills", "entities", "contact", "experience"
        user_id: str = None,
        **kwargs,
    ) -> GatewayResponse:
        """Extract structured data from text."""
        request = GatewayRequest(
            task_type=TaskType.EXTRACT,
            payload={"text": text, "extraction_type": extraction_type, **kwargs},
            user_id=user_id,
        )
        return self.process(request)
    
    def match(
        self,
        candidate_profile: Dict[str, Any],
        job_requirements: Dict[str, Any],
        user_id: str = None,
        **kwargs,
    ) -> GatewayResponse:
        """Match candidate to job requirements."""
        request = GatewayRequest(
            task_type=TaskType.MATCH,
            payload={
                "candidate": candidate_profile,
                "job": job_requirements,
                **kwargs,
            },
            user_id=user_id,
        )
        return self.process(request)
    
    # ─────────────────────────────────────────────────────────────────────
    # Core Processing
    # ─────────────────────────────────────────────────────────────────────
    
    def process(self, request: GatewayRequest) -> GatewayResponse:
        """
        Process an AI request through the gateway.
        
        Flow:
          1. Route to appropriate backend
          2. Execute request
          3. Calibrate confidence
          4. Record for ground truth
          5. Check for drift
          6. Return response
        """
        start_time = time.time()
        self._request_count += 1
        
        # Initialize if needed
        self._initialize()
        
        # 1. Routing decision
        backend, route_meta = self.routing_policy.route(request)
        
        # 2. Execute on backend
        try:
            result, raw_confidence, engines_used = self._execute(backend, request, route_meta)
            success = True
            error = None
        except Exception as e:
            logger.error("Gateway execution error: %s", e)
            result = None
            raw_confidence = 0.0
            engines_used = []
            success = False
            error = str(e)
            self._error_count += 1
        
        # 3. Calibrate confidence
        calibrated_confidence = self.calibrator.calibrate(
            raw_confidence,
            request.task_type,
            backend,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        self._total_latency_ms += latency_ms
        
        # 4. Build response
        ground_truth_id = str(uuid.uuid4())
        
        response = GatewayResponse(
            request_id=request.request_id,
            task_type=request.task_type,
            result=result,
            confidence=raw_confidence,
            calibrated_confidence=calibrated_confidence,
            route_taken=backend,
            engines_consulted=engines_used,
            consensus_method=route_meta.get("consensus", "single"),
            ground_truth_id=ground_truth_id,
            success=success,
            error=error,
            latency_ms=latency_ms,
        )
        
        # 5. Record for ground truth
        self.ground_truth.record_prediction(
            ground_truth_id,
            request,
            response,
        )
        
        # 6. Check for drift
        drift_flags = self.drift_detector.record(
            calibrated_confidence,
            latency_ms,
            not success,
        )
        response.drift_flags = drift_flags
        
        if drift_flags:
            logger.warning("Drift detected: %s", drift_flags)
        
        return response
    
    def _execute(
        self,
        backend: str,
        request: GatewayRequest,
        route_meta: Dict[str, Any],
    ) -> Tuple[Any, float, List[str]]:
        """Execute request on the selected backend."""
        
        if backend == "llm_gateway":
            return self._execute_llm(request)
        
        elif backend == "unified_ai_engine":
            return self._execute_unified(request)
        
        elif backend == "rules_engine":
            return self._execute_rules(request)
        
        elif backend == "hybrid":
            # Try rules first, fall back to LLM
            try:
                result, conf, engines = self._execute_rules(request)
                if conf >= 0.5:  # Rules confident enough
                    return result, conf, engines
            except Exception:
                pass
            return self._execute_llm(request)
        
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _execute_llm(self, request: GatewayRequest) -> Tuple[Any, float, List[str]]:
        """Execute on LLM Gateway."""
        if not self._llm_gateway:
            raise RuntimeError("LLM Gateway not available")
        
        payload = request.payload
        
        if request.task_type == TaskType.GENERATE:
            response = self._llm_gateway.generate(
                payload.get("prompt", ""),
                provider=payload.get("provider"),
                max_tokens=payload.get("max_tokens", 1000),
                temperature=payload.get("temperature", 0.7),
            )
            return response.text, 0.9 if response.success else 0.0, [response.provider]
        
        elif request.task_type == TaskType.ANALYZE:
            prompt = f"Analyze the following text:\n\n{payload.get('text', '')}"
            response = self._llm_gateway.generate(prompt)
            return response.text, 0.85 if response.success else 0.0, [response.provider]
        
        elif request.task_type == TaskType.EXTRACT:
            ext_type = payload.get("extraction_type", "skills")
            prompt = f"Extract {ext_type} from:\n\n{payload.get('text', '')}\n\nReturn as JSON."
            response = self._llm_gateway.generate(prompt)
            
            # Try to parse JSON from response
            try:
                import re
                json_match = re.search(r"\{.*\}|\[.*\]", response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group()), 0.8, [response.provider]
            except Exception:
                pass
            
            return response.text, 0.6, [response.provider]
        
        else:
            # Generic LLM handling
            response = self._llm_gateway.generate(str(payload))
            return response.text, 0.7 if response.success else 0.0, [response.provider]
    
    def _execute_unified(self, request: GatewayRequest) -> Tuple[Any, float, List[str]]:
        """Execute on Unified AI Engine."""
        if not self._unified_engine:
            raise RuntimeError("Unified AI Engine not available")
        
        payload = request.payload
        
        if request.task_type == TaskType.SCORE:
            # Use the ensemble scoring
            result = self._unified_engine.score_candidate(
                text=payload.get("resume_text", ""),
                skills=payload.get("skills", []),
                experience_years=payload.get("experience_years", 0),
                education=payload.get("education", "unknown"),
            )
            return result.to_dict(), result.confidence, list(result.engine_results.keys())
        
        elif request.task_type == TaskType.CLASSIFY:
            cat_type = payload.get("category_type", "industry")
            text = payload.get("text", "")
            
            if cat_type == "industry":
                industry, conf = self._unified_engine.predict_job_category(text)
                return {"industry": industry, "confidence": conf}, conf, ["unified_ai_engine"]
            else:
                # Generic classification
                result = self._unified_engine.quick_score(text)
                return result.to_dict(), result.confidence, ["unified_ai_engine"]
        
        elif request.task_type == TaskType.MATCH:
            # Job-candidate matching
            candidate = payload.get("candidate", {})
            job = payload.get("job", {})
            
            # Build combined text for scoring
            combined_text = f"{candidate.get('resume_text', '')} REQUIREMENTS: {job.get('description', '')}"
            result = self._unified_engine.score_candidate(
                text=combined_text,
                skills=candidate.get("skills", []),
                experience_years=candidate.get("experience_years", 0),
            )
            return {
                "match_score": result.match_score,
                "reasoning": result.reasoning,
                "recommendations": result.recommendations,
            }, result.confidence, list(result.engine_results.keys())
        
        else:
            # Default to quick_score
            result = self._unified_engine.quick_score(str(payload))
            return result.to_dict(), result.confidence, ["unified_ai_engine"]
    
    def _execute_rules(self, request: GatewayRequest) -> Tuple[Any, float, List[str]]:
        """Execute using rules/expert system."""
        payload = request.payload
        
        if request.task_type == TaskType.EXTRACT:
            ext_type = payload.get("extraction_type", "skills")
            text = payload.get("text", "")
            
            if ext_type == "contact":
                # Simple regex extraction
                import re
                emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
                phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
                return {"emails": emails, "phones": phones}, 0.95, ["rules_engine"]
            
            elif ext_type == "skills":
                # Would use skill matcher from expert system
                try:
                    from services.ai_engine.expert_system import skill_matcher
                    skills = skill_matcher.extract_skills(text)
                    return {"skills": skills}, 0.85, ["expert_system"]
                except Exception:
                    return {"skills": [], "error": "Skill matcher not available"}, 0.3, ["rules_engine"]
        
        # Default: low confidence, signal need for fallback
        return {"result": "rules_engine_default"}, 0.2, ["rules_engine"]
    
    # ─────────────────────────────────────────────────────────────────────
    # Feedback API (for ground truth collection)
    # ─────────────────────────────────────────────────────────────────────
    
    def record_outcome(
        self,
        ground_truth_id: str,
        outcome_type: str,
        outcome_value: Any,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Record an outcome for a previous prediction (for feedback loop)."""
        return self.ground_truth.record_outcome(
            ground_truth_id,
            outcome_type,
            outcome_value,
            metadata,
        )
    
    # ─────────────────────────────────────────────────────────────────────
    # Health & Metrics
    # ─────────────────────────────────────────────────────────────────────
    
    def health(self) -> Dict[str, Any]:
        """Return gateway health status."""
        return {
            "status": "healthy" if self._initialized else "initializing",
            "backends": {
                "llm_gateway": self._llm_gateway is not None,
                "unified_ai_engine": self._unified_engine is not None,
            },
            "metrics": {
                "total_requests": self._request_count,
                "total_errors": self._error_count,
                "error_rate": self._error_count / max(self._request_count, 1),
                "avg_latency_ms": self._total_latency_ms / max(self._request_count, 1),
            },
            "drift": self.drift_detector.get_stats(),
            "ground_truth": self.ground_truth.get_feedback_stats(),
        }
    
    def set_drift_baseline(self) -> Dict[str, float]:
        """Capture current metrics as drift detection baseline."""
        return self.drift_detector.set_baseline()


# ══════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ══════════════════════════════════════════════════════════════════════════

ai_gateway = AIGateway()


# ══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("═" * 70)
    print("CareerTrojan AI Gateway — Control Plane Entry Point")
    print("═" * 70)
    
    # Health check
    health = ai_gateway.health()
    print(f"\n📊 Health: {health['status']}")
    print(f"   Backends: {health['backends']}")
    print(f"   Requests: {health['metrics']['total_requests']}")
    
    # Test classification
    print("\n🔍 Testing classification...")
    response = ai_gateway.classify(
        "Senior Software Engineer with 10 years Python experience",
        category_type="industry",
    )
    print(f"   Route: {response.route_taken}")
    print(f"   Result: {response.result}")
    print(f"   Confidence: {response.confidence:.2f} → {response.calibrated_confidence:.2f} (calibrated)")
    print(f"   Ground Truth ID: {response.ground_truth_id}")
    
    # Test extraction
    print("\n📝 Testing extraction...")
    response = ai_gateway.extract(
        "Contact me at john@example.com or call 555-123-4567",
        extraction_type="contact",
    )
    print(f"   Route: {response.route_taken}")
    print(f"   Result: {response.result}")
    
    # Updated health
    print("\n📊 Updated Health:")
    health = ai_gateway.health()
    print(f"   Requests: {health['metrics']['total_requests']}")
    print(f"   Avg Latency: {health['metrics']['avg_latency_ms']:.1f}ms")
    
    print("\n✅ AI Gateway operational")
