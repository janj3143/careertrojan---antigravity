# IntelliCV AI Backend API

**FastAPI-based REST API for AI model training and prediction services**

---

## 🚀 Quick Start

### Install Dependencies

```powershell
cd c:\IntelliCV-AI\IntelliCV\SANDBOX\admin_portal\backend\api
pip install -r requirements.txt
```

### Start the Server

```powershell
python main.py
```

Or with uvicorn directly:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📋 API Endpoints

### Health & Status

- **GET /** - Root health check
- **GET /health** - Detailed health check
- **GET /api/v1/status** - System status with engine metrics

### Predictions

- **POST /api/v1/predict** - Ensemble prediction (all engines vote)
- **POST /api/v1/predict/neural** - Neural network prediction only
- **POST /api/v1/predict/expert** - Expert system validation

### Feedback

- **POST /api/v1/feedback** - Submit prediction feedback
- **GET /api/v1/feedback/performance** - Get engine performance metrics

### Training

- **POST /api/v1/training/scenarios** - Create training scenario
- **GET /api/v1/training/scenarios** - List all scenarios
- **POST /api/v1/training/train** - Train a model (background task)
- **GET /api/v1/training/review_queue** - Get review queue

### Expert System Rules

- **POST /api/v1/rules** - Create new rule
- **GET /api/v1/rules** - List all rules
- **PUT /api/v1/rules/{rule_id}** - Update rule
- **DELETE /api/v1/rules/{rule_id}** - Delete rule

---

## 🔧 Example Usage

### Make a Prediction

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={
        "input_data": {
            "job_title": "Senior Software Engineer",
            "experience_years": 8,
            "skills": ["Python", "FastAPI", "Docker"]
        },
        "task": "job_title_classifier"
    }
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']}")
```

### Submit Feedback

```python
response = requests.post(
    "http://localhost:8000/api/v1/feedback",
    json={
        "prediction_id": "pred_12345",
        "original_prediction": "Senior Developer",
        "user_correction": "Senior Software Engineer",
        "context": {"source": "cv_parser"}
    }
)

print(f"Feedback ID: {response.json()['feedback_id']}")
```

### Create Training Scenario

```python
response = requests.post(
    "http://localhost:8000/api/v1/training/scenarios",
    json={
        "scenario_id": "custom_classifier",
        "name": "Custom Job Classifier",
        "description": "Classifies custom job categories",
        "task_type": "classification",
        "config": {
            "model_type": "neural_network",
            "confidence_threshold": 0.75
        }
    }
)

print(f"Scenario created: {response.json()['scenario_id']}")
```

---

## 🏗️ Architecture

### Engine Initialization

On startup, the API initializes all 4 AI engines:
1. **Model Trainer** - Manages training scenarios
2. **Neural Network Engine** - Deep learning predictions
3. **Expert System Engine** - Rule-based validation
4. **Feedback Loop Engine** - Ensemble voting & learning

### Background Tasks

Training and feedback distribution run as background tasks:
- Training doesn't block API responses
- Feedback is distributed asynchronously
- Performance updates happen in real-time

### Data Persistence

All engines auto-save to disk:
- Rules: `backend/data/rules/expert_rules.json`
- Feedback: `backend/data/feedback/feedback_queue.json`
- Performance: `backend/data/feedback/engine_performance.json`
- Models: `backend/data/models/[scenario_id]/`

---

## 🔒 Security Considerations

**For Production:**

1. **CORS:** Configure `allow_origins` appropriately
2. **Authentication:** Add JWT or API key middleware
3. **Rate Limiting:** Implement rate limiting on endpoints
4. **HTTPS:** Use TLS/SSL certificates
5. **Input Validation:** Already handled by Pydantic models

---

## 📊 Monitoring

### Check Engine Status

```python
response = requests.get("http://localhost:8000/api/v1/status")
status = response.json()

print(f"Scenarios: {status['model_trainer']['scenarios_count']}")
print(f"Review Queue: {status['model_trainer']['review_queue_size']}")
print(f"Rules: {status['expert_system']['rules_count']}")
```

### Get Performance Metrics

```python
response = requests.get("http://localhost:8000/api/v1/feedback/performance")
performance = response.json()

for engine, metrics in performance.items():
    print(f"{engine}: {metrics['accuracy']:.2%} accuracy")
```

---

## 🐛 Troubleshooting

### Port Already in Use

```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# Or use different port
uvicorn main:app --reload --port 8001
```

### Import Errors

Ensure backend path is in PYTHONPATH:
```python
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
```

### Engine Not Initialized

Check logs and ensure all dependencies installed:
```powershell
pip install -r requirements.txt
```

---

## 📖 Interactive Documentation

FastAPI provides automatic interactive docs:

1. **Swagger UI:** http://localhost:8000/docs
   - Try out endpoints
   - See request/response schemas
   - Test authentication

2. **ReDoc:** http://localhost:8000/redoc
   - Clean documentation view
   - Export API spec
   - Share with team

---

## 🚀 Deployment

### Development

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Production

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Created:** October 14, 2025
