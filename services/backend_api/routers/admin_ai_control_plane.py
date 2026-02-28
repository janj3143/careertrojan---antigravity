"""
CareerTrojan — Control Plane API Router
========================================

FastAPI router exposing Control Plane capabilities to admin dashboard.

Endpoints:
    /ai/gateway/* - Unified AI Gateway endpoints
    /ai/outcomes/* - Ground-truth tracking
    /ai/evaluation/* - Golden tests and metrics
    /ai/routing/* - Routing policy management
    /ai/calibration/* - Confidence calibration
    /ai/drift/* - Drift monitoring and alerts

Author: CareerTrojan System
Date:   February 2026
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.backend_api.utils.auth_deps import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Control Plane"], dependencies=[Depends(require_admin)])


# ── Pydantic Models ──────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    text: str = Field(..., description="CV/profile text to score")
    skills: Optional[List[str]] = Field(default=None, description="List of skills")
    experience_years: int = Field(default=0, ge=0)
    education_level: str = Field(default="unknown")
    job_title: str = Field(default="")
    user_id: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Text to extract skills from")
    user_id: Optional[str] = None


class MatchRequest(BaseModel):
    cv_text: str = Field(..., description="CV text")
    jd_text: str = Field(..., description="Job description text")
    user_id: Optional[str] = None


class RewriteRequest(BaseModel):
    original_text: str = Field(..., description="Text to rewrite")
    target_role: str = Field(default="")
    style: str = Field(default="professional")
    focus_areas: Optional[List[str]] = None
    user_id: Optional[str] = None


class QARequest(BaseModel):
    question: str = Field(..., description="Career question")
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class ChartRequest(BaseModel):
    chart_type: str = Field(..., description="Chart type: spider, covery_quadrant, skill_gap, etc.")
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class QuestionsRequest(BaseModel):
    target_role: str = Field(..., description="Target job role")
    company: str = Field(default="")
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class OutcomeRequest(BaseModel):
    request_id: str = Field(..., description="Original AI request ID")
    outcome_type: str = Field(..., description="Type of outcome")
    outcome_value: Any = Field(..., description="Outcome value")
    user_id: Optional[str] = None


class CustomRuleRequest(BaseModel):
    name: str = Field(..., description="Rule name")
    strategy: str = Field(..., description="Routing strategy")
    conditions: Dict[str, Any] = Field(..., description="Matching conditions")
    priority: int = Field(default=0)


class CalibrationTrainRequest(BaseModel):
    task_type: str = Field(..., description="Task type to train calibration for")
    method: str = Field(default="isotonic", description="Calibration method")


# ── Gateway Endpoints ────────────────────────────────────────────────────

@router.post("/gateway/score", summary="Score a candidate CV/profile")
async def gateway_score(request: ScoreRequest):
    """Score a candidate using all AI engines."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.score_candidate(
            text=request.text,
            skills=request.skills,
            experience_years=request.experience_years,
            education_level=request.education_level,
            job_title=request.job_title,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_score failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/extract", summary="Extract skills from text")
async def gateway_extract(request: ExtractRequest):
    """Extract skills using collocation engine."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.extract_skills(
            text=request.text,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_extract failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/match", summary="Match CV to job description")
async def gateway_match(request: MatchRequest):
    """Match CV against JD."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.match_cv_jd(
            cv_text=request.cv_text,
            jd_text=request.jd_text,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_match failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/rewrite", summary="Rewrite CV text")
async def gateway_rewrite(request: RewriteRequest):
    """Generate CV rewrite using LLM."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.rewrite_cv(
            original_text=request.original_text,
            target_role=request.target_role,
            style=request.style,
            focus_areas=request.focus_areas,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_rewrite failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/qa", summary="Answer career question")
async def gateway_qa(request: QARequest):
    """Answer career question using LLM."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.career_qa(
            question=request.question,
            context=request.context,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_qa failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/chart", summary="Get chart data")
async def gateway_chart(request: ChartRequest):
    """Generate visualization data."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.get_chart_data(
            chart_type=request.chart_type,
            context=request.context,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_chart failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/questions", summary="Generate interview questions")
async def gateway_questions(request: QuestionsRequest):
    """Generate smart interview questions."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        
        response = gateway.generate_smart_questions(
            target_role=request.target_role,
            company=request.company,
            context=request.context,
            user_id=request.user_id,
            role="admin",
        )
        
        return response.to_dict()
    except Exception as e:
        logger.exception("gateway_questions failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gateway/stats", summary="Get gateway statistics")
async def gateway_stats():
    """Get gateway usage statistics."""
    try:
        from services.ai_engine.control_plane import get_gateway
        gateway = get_gateway()
        return gateway.get_stats()
    except Exception as e:
        logger.exception("gateway_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Outcome Tracking Endpoints ───────────────────────────────────────────

@router.post("/outcomes/record", summary="Record an outcome")
async def record_outcome(request: OutcomeRequest):
    """Record ground-truth outcome for correlation."""
    try:
        from services.ai_engine.control_plane import get_outcome_tracker
        tracker = get_outcome_tracker()
        
        success = tracker.record(
            request_id=request.request_id,
            outcome_type=request.outcome_type,
            outcome_value=request.outcome_value,
            user_id=request.user_id,
        )
        
        return {"success": success}
    except Exception as e:
        logger.exception("record_outcome failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outcomes/rates/{outcome_type}", summary="Get outcome rates")
async def get_outcome_rates(
    outcome_type: str,
    days: int = Query(default=30, ge=1, le=365),
):
    """Get outcome rates for a specific type."""
    try:
        from services.ai_engine.control_plane import get_outcome_tracker
        tracker = get_outcome_tracker()
        return tracker.get_outcome_rates(outcome_type, days=days)
    except Exception as e:
        logger.exception("get_outcome_rates failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outcomes/stats", summary="Get outcome tracker statistics")
async def get_outcome_stats():
    """Get outcome tracker statistics."""
    try:
        from services.ai_engine.control_plane import get_outcome_tracker
        tracker = get_outcome_tracker()
        return tracker.get_stats()
    except Exception as e:
        logger.exception("get_outcome_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Evaluation Endpoints ─────────────────────────────────────────────────

@router.get("/evaluation/suites", summary="List test suites")
async def list_test_suites():
    """List available golden test suites."""
    try:
        from services.ai_engine.control_plane import get_evaluator
        evaluator = get_evaluator()
        return evaluator.get_stats()
    except Exception as e:
        logger.exception("list_test_suites failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluation/run/{suite}", summary="Run test suite")
async def run_test_suite(suite: str):
    """Run a specific golden test suite."""
    try:
        from services.ai_engine.control_plane import get_evaluator
        evaluator = get_evaluator()
        report = evaluator.run_suite(suite)
        return report.to_dict()
    except Exception as e:
        logger.exception("run_test_suite failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluation/run-all", summary="Run all test suites")
async def run_all_tests():
    """Run all golden test suites."""
    try:
        from services.ai_engine.control_plane import get_evaluator
        evaluator = get_evaluator()
        reports = evaluator.run_golden_tests()
        return {k: v.to_dict() for k, v in reports.items()}
    except Exception as e:
        logger.exception("run_all_tests failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/regression", summary="Check for regression")
async def check_regression(threshold: float = Query(default=0.05, ge=0.01, le=0.5)):
    """Check for regression against historical results."""
    try:
        from services.ai_engine.control_plane import get_evaluator
        evaluator = get_evaluator()
        is_regressed, details = evaluator.check_regression(threshold=threshold)
        return {"is_regressed": is_regressed, "details": details}
    except Exception as e:
        logger.exception("check_regression failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Routing Endpoints ────────────────────────────────────────────────────

@router.get("/routing/stats", summary="Get routing statistics")
async def get_routing_stats():
    """Get routing policy statistics."""
    try:
        from services.ai_engine.control_plane import get_router
        router_policy = get_router()
        return router_policy.get_stats()
    except Exception as e:
        logger.exception("get_routing_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/explain", summary="Explain routing decision")
async def explain_routing(
    task_type: str,
    latency_class: str = Query(default="interactive"),
    user_role: str = Query(default="user"),
):
    """Get explanation for a routing decision."""
    try:
        from services.ai_engine.control_plane import get_router
        router_policy = get_router()
        return {"explanation": router_policy.explain_decision(task_type, latency_class=latency_class, user_role=user_role)}
    except Exception as e:
        logger.exception("explain_routing failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/rules", summary="Add custom routing rule")
async def add_routing_rule(request: CustomRuleRequest):
    """Add a custom routing rule."""
    try:
        from services.ai_engine.control_plane import get_router
        router_policy = get_router()
        
        success = router_policy.add_custom_rule(
            name=request.name,
            strategy=request.strategy,
            conditions=request.conditions,
            priority=request.priority,
        )
        
        return {"success": success}
    except Exception as e:
        logger.exception("add_routing_rule failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/routing/rules/{name}", summary="Remove custom routing rule")
async def remove_routing_rule(name: str):
    """Remove a custom routing rule."""
    try:
        from services.ai_engine.control_plane import get_router
        router_policy = get_router()
        success = router_policy.remove_custom_rule(name)
        return {"success": success}
    except Exception as e:
        logger.exception("remove_routing_rule failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Calibration Endpoints ────────────────────────────────────────────────

@router.get("/calibration/stats", summary="Get calibration statistics")
async def get_calibration_stats():
    """Get confidence calibration statistics."""
    try:
        from services.ai_engine.control_plane import get_calibrator
        calibrator = get_calibrator()
        return calibrator.get_stats()
    except Exception as e:
        logger.exception("get_calibration_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibration/metrics/{task_type}", summary="Get calibration metrics")
async def get_calibration_metrics(task_type: str):
    """Get calibration metrics for a task type."""
    try:
        from services.ai_engine.control_plane import get_calibrator
        calibrator = get_calibrator()
        metrics = calibrator.get_calibration_metrics(task_type)
        return metrics.to_dict()
    except Exception as e:
        logger.exception("get_calibration_metrics failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibration/train", summary="Train calibration model")
async def train_calibration(request: CalibrationTrainRequest):
    """Train calibration model from ground-truth data."""
    try:
        from services.ai_engine.control_plane import get_calibrator
        calibrator = get_calibrator()
        success = calibrator.auto_calibrate(request.task_type)
        return {"success": success}
    except Exception as e:
        logger.exception("train_calibration failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibration/demo", summary="Demo calibration")
async def demo_calibration(
    raw_confidence: float = Query(..., ge=0, le=1),
    task_type: str = Query(default="score"),
):
    """Demonstrate calibration on a confidence value."""
    try:
        from services.ai_engine.control_plane import get_calibrator
        calibrator = get_calibrator()
        calibrated = calibrator.calibrate(raw_confidence, task_type)
        return {
            "raw_confidence": raw_confidence,
            "calibrated_confidence": calibrated,
            "task_type": task_type,
        }
    except Exception as e:
        logger.exception("demo_calibration failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Drift Detection Endpoints ────────────────────────────────────────────

@router.get("/drift/report", summary="Get drift report")
async def get_drift_report():
    """Get comprehensive drift analysis report."""
    try:
        from services.ai_engine.control_plane import get_drift_detector
        detector = get_drift_detector()
        report = detector.get_drift_report()
        return report.to_dict()
    except Exception as e:
        logger.exception("get_drift_report failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/alerts", summary="Get recent alerts")
async def get_drift_alerts(limit: int = Query(default=50, ge=1, le=500)):
    """Get recent drift alerts."""
    try:
        from services.ai_engine.control_plane import get_drift_detector
        detector = get_drift_detector()
        alerts = detector.get_recent_alerts(limit=limit)
        return {"alerts": [a.to_dict() for a in alerts]}
    except Exception as e:
        logger.exception("get_drift_alerts failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drift/alerts/{alert_id}/acknowledge", summary="Acknowledge alert")
async def acknowledge_alert(alert_id: str):
    """Acknowledge a drift alert."""
    try:
        from services.ai_engine.control_plane import get_drift_detector
        detector = get_drift_detector()
        success = detector.acknowledge_alert(alert_id)
        return {"success": success}
    except Exception as e:
        logger.exception("acknowledge_alert failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/trends/{task_type}", summary="Get historical trends")
async def get_drift_trends(
    task_type: str,
    metric: str = Query(default="confidence"),
    days: int = Query(default=30, ge=1, le=365),
):
    """Get historical trend data for visualization."""
    try:
        from services.ai_engine.control_plane import get_drift_detector
        detector = get_drift_detector()
        return detector.get_historical_trends(task_type, metric=metric, days=days)
    except Exception as e:
        logger.exception("get_drift_trends failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/stats", summary="Get drift detector statistics")
async def get_drift_stats():
    """Get drift detector statistics."""
    try:
        from services.ai_engine.control_plane import get_drift_detector
        detector = get_drift_detector()
        return detector.get_stats()
    except Exception as e:
        logger.exception("get_drift_stats failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health Check ─────────────────────────────────────────────────────────

@router.get("/health/detailed", summary="Control Plane detailed health check")
async def control_plane_health():
    """Check health of all Control Plane components (admin detail view)."""
    health = {
        "gateway": False,
        "outcome_tracker": False,
        "evaluator": False,
        "routing": False,
        "calibrator": False,
        "drift_detector": False,
    }
    
    try:
        from services.ai_engine.control_plane import get_gateway
        get_gateway()
        health["gateway"] = True
    except Exception:
        pass
    
    try:
        from services.ai_engine.control_plane import get_outcome_tracker
        get_outcome_tracker()
        health["outcome_tracker"] = True
    except Exception:
        pass
    
    try:
        from services.ai_engine.control_plane import get_evaluator
        get_evaluator()
        health["evaluator"] = True
    except Exception:
        pass
    
    try:
        from services.ai_engine.control_plane import get_router
        get_router()
        health["routing"] = True
    except Exception:
        pass
    
    try:
        from services.ai_engine.control_plane import get_calibrator
        get_calibrator()
        health["calibrator"] = True
    except Exception:
        pass
    
    try:
        from services.ai_engine.control_plane import get_drift_detector
        get_drift_detector()
        health["drift_detector"] = True
    except Exception:
        pass
    
    all_healthy = all(health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": health,
        "healthy_count": sum(health.values()),
        "total_components": len(health),
    }
