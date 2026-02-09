
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
FastAPI and Flask integration for CompanyIntel enrichment engine.
Provides REST endpoints for enrichment, batch processing, and company data access.
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
import json
import uvicorn
from services.company_intelligence_parser import CompanyIntel

app = FastAPI(title="IntelliCV Company Intelligence API")
ci = CompanyIntel()

@app.get("/enrich")
def enrich_company(name: str = Query(..., description="Company name to enrich")):
    rec = ci.enrich(name)
    return JSONResponse(content=rec.asdict())

@app.get("/enrich_many")
def enrich_many(companies: List[str] = Query(..., description="List of company names")):
    recs = ci.enrich_many(companies)
    return JSONResponse(content=[r.asdict() for r in recs])

@app.get("/companies")
def get_companies():
    json_path = Path(ci.JSON_EXPORT)
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content=[])

# Flask version for compatibility
from flask import Flask, request, jsonify
flask_app = Flask("intelliCV_company_intel")

@flask_app.route("/enrich", methods=["GET"])
def flask_enrich():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    rec = ci.enrich(name)
    return jsonify(rec.asdict())

@flask_app.route("/enrich_many", methods=["GET"])
def flask_enrich_many():
    companies = request.args.getlist("companies")
    if not companies:
        return jsonify({"error": "Missing 'companies' parameter"}), 400
    recs = ci.enrich_many(companies)
    return jsonify([r.asdict() for r in recs])

@flask_app.route("/companies", methods=["GET"])
def flask_get_companies():
    json_path = Path(ci.JSON_EXPORT)
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == "__main__":
    # To run FastAPI: uvicorn services.company_intelligence_api:app --reload
    # To run Flask: python services/company_intelligence_api.py
    import sys
    if "flask" in sys.argv:
        flask_app.run(host="0.0.0.0", port=8000)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
