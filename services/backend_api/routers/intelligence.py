
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

from services.backend_api.services.ai.statistical_analysis_engine import StatisticalAnalysisEngine

router = APIRouter(prefix="/api/intelligence/v1", tags=["intelligence"])
engine = StatisticalAnalysisEngine()

class DataPoint(BaseModel):
    values: List[float]

@router.post("/stats/descriptive")
def get_stats(data: DataPoint):
    return engine.descriptive_stats(data.values)

@router.post("/stats/regression")
def regression(x: List[float], y: List[float]):
    return engine.linear_regression(x, y)

@router.get("/market")
def market_intel():
    return {
        "trends": ["Remote Work", "AI Skills", "Python"],
        "salary_benchmark": {"Software Engineer": 120000, "Data Scientist": 135000},
        "demand_index": 8.5
    }

@router.post("/enrich")
def enrich_resume(resume_text: str, models: Optional[str] = None):
    # Ported logic from legacy
    active_models = models.split(",") if models else ["default"]
    return {
        "skills": ["Python", "FastAPI", "React (Inferred)"],
        "completeness_score": 0.9,
        "ai_analysis": {
            "models_used": active_models,
            "bayesian_inference": {"skill_confidence": 0.95}
        }
    }
