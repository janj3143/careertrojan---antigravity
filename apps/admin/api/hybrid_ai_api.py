
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

"""
Hybrid AI Harness API Endpoint
- Exposes the HybridAIHarness orchestrator as a REST API for UI and external integration
- Supports async, smart routing, and fusion of enrichment results
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from advanced_enrichment_upgrades.hybrid_ai_harness import HybridAIHarness
import uvicorn

app = FastAPI()
harness = HybridAIHarness()

@app.post("/api/enrich")
async def enrich(request: Request):
    """
    Unified enrichment endpoint: accepts user/job/profile data and returns fused enrichment results.
    """
    try:
        data = await request.json()
        user_data = data.get("user_data", {})
        job_data = data.get("job_data", {})
        # Call the orchestrator (can be made async/future for perf)
        result = harness.enrich_user_profile(user_data, job_data)
        return JSONResponse(content={"success": True, "enrichment": result})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

# Optional: add health check, version, and admin endpoints as needed

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
