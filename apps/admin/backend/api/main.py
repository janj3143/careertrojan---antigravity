"""
Backend API Server - Main Entry Point
Provides REST API endpoints for all AI services

Created: October 14, 2025
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import logging
from pathlib import Path
import sys
from datetime import datetime
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import AI services
from ai_services.model_trainer import ModelTrainer, TrainingScenario
from ai_services.neural_network_engine import NeuralNetworkEngine
from ai_services.expert_system_engine import ExpertSystemEngine, Rule
from ai_services.feedback_loop_engine import FeedbackLoopEngine

# Import portal integration services
try:
    from backend.unified_ai_engine import UnifiedAIEngine
    from backend.resume_parser import resume_parser
    from backend.ai_chat_integration import ai_chat_integration
    from backend.company_intelligence_api import company_intelligence_api
    PORTAL_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Portal services not available: {e}")
    PORTAL_SERVICES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IntelliCV AI Backend API",
    description="REST API for AI model training and prediction services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
model_trainer: Optional[ModelTrainer] = None
neural_network: Optional[NeuralNetworkEngine] = None
expert_system: Optional[ExpertSystemEngine] = None
feedback_loop: Optional[FeedbackLoopEngine] = None

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class PredictionRequest(BaseModel):
    """Request model for predictions"""
    input_data: Dict[str, Any]
    task: str
    engines: Optional[List[str]] = None  # If None, use all engines
    
class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: Any
    confidence: float
    engine_votes: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str

class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    prediction_id: str
    original_prediction: Any
    user_correction: Any
    context: Dict[str, Any]
    
class TrainingScenarioRequest(BaseModel):
    """Request model for creating training scenarios"""
    scenario_id: str
    name: str
    description: str
    task_type: str
    config: Dict[str, Any]
    
class TrainingRequest(BaseModel):
    """Request model for training a model"""
    scenario_id: str
    epochs: Optional[int] = 10
    batch_size: Optional[int] = 32
    learning_rate: Optional[float] = 0.001
    
class RuleRequest(BaseModel):
    """Request model for creating/updating rules"""
    rule_id: str
    name: str
    description: str
    condition: str
    action: str
    priority: int = Field(ge=1, le=10)
    category: str
    enabled: bool = True

class HealthResponse(BaseModel):
    """Response model for health checks"""
    status: str
    timestamp: str
    engines: Dict[str, str]
    version: str

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize all AI engines on startup"""
    global model_trainer, neural_network, expert_system, feedback_loop
    
    logger.info("Starting up IntelliCV AI Backend API...")
    
    try:
        # Initialize engines
        model_trainer = ModelTrainer()
        neural_network = NeuralNetworkEngine()
        expert_system = ExpertSystemEngine()
        feedback_loop = FeedbackLoopEngine()
        
        # Register engines with feedback loop
        feedback_loop.register_engine("neural_network", neural_network, initial_weight=0.85)
        feedback_loop.register_engine("expert_system", expert_system, initial_weight=0.80)
        
        logger.info("All AI engines initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize engines: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down IntelliCV AI Backend API...")
    
    # Save any pending data
    if feedback_loop:
        feedback_loop._save_feedback_queue()
        feedback_loop._save_engine_performance()
    
    if expert_system:
        expert_system._save_rules()

# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "engines": {
            "model_trainer": "initialized" if model_trainer else "not initialized",
            "neural_network": "initialized" if neural_network else "not initialized",
            "expert_system": "initialized" if expert_system else "not initialized",
            "feedback_loop": "initialized" if feedback_loop else "not initialized"
        },
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    return await root()

@app.get("/api/v1/status")
async def get_status():
    """Get detailed system status"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "model_trainer": {
                "scenarios_count": len(model_trainer.scenarios) if model_trainer else 0,
                "review_queue_size": len(model_trainer.review_queue) if model_trainer else 0
            },
            "neural_network": {
                "embeddings_cached": len(neural_network.embeddings_cache) if neural_network else 0,
                "feedback_buffer_size": len(neural_network.feedback_buffer) if neural_network else 0
            },
            "expert_system": {
                "rules_count": len(expert_system.rules) if expert_system else 0,
                "enabled_rules": sum(1 for r in expert_system.rules.values() if r.enabled) if expert_system else 0
            },
            "feedback_loop": {
                "engines_count": len(feedback_loop.engines) if feedback_loop else 0,
                "feedback_queue_size": len(feedback_loop.feedback_queue) if feedback_loop else 0,
                "feedback_history_size": len(feedback_loop.feedback_history) if feedback_loop else 0
            }
        }
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Prediction Endpoints
# ============================================================================

@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make a prediction using ensemble voting"""
    try:
        if not feedback_loop:
            raise HTTPException(status_code=503, detail="Feedback loop engine not initialized")
        
        # Get ensemble prediction
        result = feedback_loop.ensemble_predict(
            input_data=request.input_data,
            task=request.task,
            engines_to_use=request.engines
        )
        
        return {
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "engine_votes": result.get("votes", []),
            "metadata": result.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/predict/neural")
async def predict_neural(request: PredictionRequest):
    """Make a prediction using neural network only"""
    try:
        if not neural_network:
            raise HTTPException(status_code=503, detail="Neural network engine not initialized")
        
        prediction, confidence, metadata = neural_network.predict_with_confidence(
            input_data=request.input_data,
            task=request.task
        )
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Neural network prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/predict/expert")
async def predict_expert(request: PredictionRequest):
    """Validate a prediction using expert system"""
    try:
        if not expert_system:
            raise HTTPException(status_code=503, detail="Expert system engine not initialized")
        
        # Expect prediction in input_data
        prediction = request.input_data.get("prediction")
        context = request.input_data.get("context", {})
        category = request.task
        
        is_valid, triggered_rules, explanation = expert_system.validate_prediction(
            prediction=prediction,
            context=context,
            category=category
        )
        
        return {
            "is_valid": is_valid,
            "triggered_rules": triggered_rules,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expert system validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Feedback Endpoints
# ============================================================================

@app.post("/api/v1/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Submit feedback for a prediction"""
    try:
        if not feedback_loop:
            raise HTTPException(status_code=503, detail="Feedback loop engine not initialized")
        
        # Submit feedback
        feedback_id = feedback_loop.submit_feedback(
            original_prediction=request.original_prediction,
            user_correction=request.user_correction,
            context=request.context
        )
        
        # Distribute feedback in background
        background_tasks.add_task(feedback_loop.distribute_feedback, feedback_id)
        
        return {
            "feedback_id": feedback_id,
            "status": "submitted",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/feedback/performance")
async def get_performance():
    """Get engine performance metrics"""
    try:
        if not feedback_loop:
            raise HTTPException(status_code=503, detail="Feedback loop engine not initialized")
        
        performance = feedback_loop.get_performance_report()
        return JSONResponse(content=performance)
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Training Endpoints
# ============================================================================

@app.post("/api/v1/training/scenarios")
async def create_scenario(request: TrainingScenarioRequest):
    """Create a new training scenario"""
    try:
        if not model_trainer:
            raise HTTPException(status_code=503, detail="Model trainer not initialized")
        
        scenario = TrainingScenario(
            scenario_id=request.scenario_id,
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            config=request.config
        )
        
        model_trainer.add_scenario(scenario)
        
        return {
            "scenario_id": request.scenario_id,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scenario creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/training/scenarios")
async def list_scenarios():
    """List all training scenarios"""
    try:
        if not model_trainer:
            raise HTTPException(status_code=503, detail="Model trainer not initialized")
        
        scenarios = {
            sid: {
                "scenario_id": s.scenario_id,
                "name": s.name,
                "description": s.description,
                "task_type": s.task_type,
                "status": s.status,
                "model_version": s.model_version,
                "performance_metrics": s.performance_metrics
            }
            for sid, s in model_trainer.scenarios.items()
        }
        
        return JSONResponse(content=scenarios)
        
    except Exception as e:
        logger.error(f"Scenarios list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/training/train")
async def train_model(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Train a model for a scenario (background task)"""
    try:
        if not model_trainer:
            raise HTTPException(status_code=503, detail="Model trainer not initialized")
        
        # Start training in background
        background_tasks.add_task(
            model_trainer.train_scenario,
            request.scenario_id,
            request.epochs,
            request.batch_size,
            request.learning_rate
        )
        
        return {
            "scenario_id": request.scenario_id,
            "status": "training_started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/training/review_queue")
async def get_review_queue():
    """Get predictions pending review"""
    try:
        if not model_trainer:
            raise HTTPException(status_code=503, detail="Model trainer not initialized")
        
        return JSONResponse(content={"review_queue": model_trainer.review_queue})
        
    except Exception as e:
        logger.error(f"Review queue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Expert System Rule Endpoints
# ============================================================================

@app.post("/api/v1/rules")
async def create_rule(request: RuleRequest):
    """Create a new expert system rule"""
    try:
        if not expert_system:
            raise HTTPException(status_code=503, detail="Expert system not initialized")
        
        rule = Rule(
            rule_id=request.rule_id,
            name=request.name,
            description=request.description,
            condition=request.condition,
            action=request.action,
            priority=request.priority,
            enabled=request.enabled,
            category=request.category
        )
        
        expert_system.add_rule(rule)
        
        return {
            "rule_id": request.rule_id,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rule creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/rules")
async def list_rules():
    """List all expert system rules"""
    try:
        if not expert_system:
            raise HTTPException(status_code=503, detail="Expert system not initialized")
        
        rules = {
            rid: {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "action": r.action,
                "priority": r.priority,
                "enabled": r.enabled,
                "category": r.category,
                "trigger_count": r.trigger_count
            }
            for rid, r in expert_system.rules.items()
        }
        
        return JSONResponse(content=rules)
        
    except Exception as e:
        logger.error(f"Rules list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/rules/{rule_id}")
async def update_rule(rule_id: str, request: RuleRequest):
    """Update an existing rule"""
    try:
        if not expert_system:
            raise HTTPException(status_code=503, detail="Expert system not initialized")
        
        updated_rule = Rule(
            rule_id=request.rule_id,
            name=request.name,
            description=request.description,
            condition=request.condition,
            action=request.action,
            priority=request.priority,
            enabled=request.enabled,
            category=request.category
        )
        
        expert_system.update_rule(rule_id, updated_rule)
        
        return {
            "rule_id": rule_id,
            "status": "updated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rule update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule"""
    try:
        if not expert_system:
            raise HTTPException(status_code=503, detail="Expert system not initialized")
        
        expert_system.delete_rule(rule_id)
        
        return {
            "rule_id": rule_id,
            "status": "deleted",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rule deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Portal Bridge Integration Endpoints
# ============================================================================

class ResumeParseRequest(BaseModel):
    """Request model for resume parsing"""
    file_path: str
    resume_id: str
    extract_intelligence: bool = True

class AIEnrichmentRequest(BaseModel):
    """Request model for AI enrichment"""
    resume_data: Dict[str, Any]
    intelligence_types: Optional[List[str]] = None

class CareerAnalysisRequest(BaseModel):
    """Request model for career trajectory analysis"""
    resume_data: Dict[str, Any]
    target_roles: Optional[List[str]] = None
    
class MarketIntelRequest(BaseModel):
    """Request model for market intelligence"""
    industry: str
    role: Optional[str] = None
    location: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for AI coaching chat"""
    message: str
    context: Dict[str, Any]
    conversation_history: Optional[List[Dict[str, str]]] = None

@app.post("/api/v1/portal/resume/parse")
async def parse_resume(request: ResumeParseRequest):
    """Parse resume and extract structured data (User Portal → Admin Backend)"""
    try:
        if not PORTAL_SERVICES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Portal services not available")
        
        # Parse resume using resume_parser
        parsed_data = resume_parser.parse_cv(
            file_path=request.file_path,
            resume_id=request.resume_id
        )
        
        # Optionally enrich with AI intelligence
        if request.extract_intelligence:
            ai_engine = UnifiedAIEngine()
            enriched_data = ai_engine.analyze_cv_comprehensive(parsed_data)
            parsed_data.update(enriched_data)
        
        return {
            "status": "success",
            "resume_id": request.resume_id,
            "parsed_data": parsed_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Resume parsing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portal/intelligence/enrich")
async def enrich_with_ai(request: AIEnrichmentRequest):
    """Enrich resume data with AI intelligence analysis"""
    try:
        if not PORTAL_SERVICES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Portal services not available")
        
        ai_engine = UnifiedAIEngine()
        
        # Perform comprehensive AI analysis
        intelligence = ai_engine.analyze_cv_comprehensive(request.resume_data)
        
        # Filter by requested intelligence types if specified
        if request.intelligence_types:
            intelligence = {
                k: v for k, v in intelligence.items()
                if k in request.intelligence_types
            }
        
        return {
            "status": "success",
            "intelligence": intelligence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI enrichment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portal/career/analyze")
async def analyze_career_trajectory(request: CareerAnalysisRequest):
    """Analyze career trajectory and provide recommendations"""
    try:
        if not PORTAL_SERVICES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Portal services not available")
        
        ai_engine = UnifiedAIEngine()
        
        # Perform career trajectory analysis
        career_analysis = ai_engine.analyze_career_trajectory(
            cv_data=request.resume_data,
            target_roles=request.target_roles or []
        )
        
        return {
            "status": "success",
            "career_trajectory": career_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Career analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portal/market/intelligence")
async def get_market_intelligence(request: MarketIntelRequest):
    """Get market intelligence data for industry/role/location"""
    try:
        if not PORTAL_SERVICES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Portal services not available")
        
        # Get market intelligence from company intelligence API
        market_data = company_intelligence_api.get_market_insights(
            industry=request.industry,
            role=request.role,
            location=request.location
        )
        
        return {
            "status": "success",
            "market_intelligence": market_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market intelligence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portal/chat/ask")
async def ai_coaching_chat(request: ChatRequest):
    """AI coaching chatbot interaction"""
    try:
        if not PORTAL_SERVICES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Portal services not available")
        
        # Get response from AI chat integration
        response = ai_chat_integration.ask(
            question=request.message,
            context=request.context,
            conversation_history=request.conversation_history or []
        )
        
        return {
            "status": "success",
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting IntelliCV AI Backend API server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
