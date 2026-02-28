import uuid
import httpx
import shutil
import os
import json
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from services.backend_api.utils.file_parser import extract_text_from_upload
from services.backend_api.routers.auth import get_current_user as require_user
from services.backend_api.services.company_intel_service import get_company_intel_service
from services.shared.paths import CareerTrojanPaths

router = APIRouter(prefix="/api/resume/v1", tags=["resume"])

# ============================================================================
# Persistent Storage Setup
# ============================================================================
# Portable: driven by shared path resolver
STORAGE_ROOT = CareerTrojanPaths().user_data
if not STORAGE_ROOT.exists():
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

RESUME_DIR = STORAGE_ROOT / "user_uploads" / "resumes"
RESUME_DIR.mkdir(parents=True, exist_ok=True)

RESUME_DB_FILE = STORAGE_ROOT / "resumes_db.json"

def load_resume_db() -> dict:
    if not RESUME_DB_FILE.exists():
        return {}
    try:
        with open(RESUME_DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_resume_db(db: dict):
    with open(RESUME_DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ============================================================================
# Models
# ============================================================================
class UploadIn(BaseModel):
    filename: str
    content_b64: str | None = None
    mime_type: str | None = None

class ResumeView(BaseModel):
    resume_id: str
    filename: str
    doc_id: str
    detected_type: str
    raw_text: str
    parsed_json: Optional[dict] = None
    ai_json: Optional[dict] = None
    warnings: list[str] = []
    timings: dict[str, float] = {}

# ============================================================================
# POST /resume/upload – Upload file
# ============================================================================
@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), auth=Depends(require_user)):
    """
    Upload a resume file, parse it, and store the result.
    """
    try:
        user_id = str(auth.id)
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        safe_filename = f"{file_id}{file_ext}"
        
        # Save file to disk
        file_path = RESUME_DIR / safe_filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Parse text from saved bytes
        file_bytes = file_path.read_bytes()
        text_content = await extract_text_from_upload(file_bytes, file.filename)
        if not text_content:
            raise HTTPException(status_code=422, detail="Unable to extract text from resume")

        parse_result = {
            "doc_id": file_id,
            "detected_type": "Resume",
            "raw_text": text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
            "word_count": len(text_content.split()),
        }

        # Company Intelligence hook (non-blocking): mine company names from uploaded text
        company_summary = {}
        try:
            company_summary = get_company_intel_service().ingest_resume_text(
                text=text_content,
                user_id=user_id,
                source="resume_upload",
            )
            parse_result["company_intel"] = company_summary
        except Exception:
            parse_result["company_intel"] = {
                "companies_found": 0,
                "companies_added": 0,
                "companies_updated": 0,
            }

        # Update DB
        db = load_resume_db()
        resume_record = {
            "resume_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "user_id": user_id,
            "uploaded_at": str(datetime.utcnow()),
            **parse_result
        }
        db[file_id] = resume_record
        save_resume_db(db)

        return {
            "ok": True,
            "data": {
                "resume_id": file_id,
                "filename": file.filename,
                "parsed_result": parse_result
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )
from datetime import datetime

# ============================================================================
# GET /resume/{resume_id} – Retrieve parsed resume
# ============================================================================
@router.get("/{resume_id}")
async def get_resume(resume_id: str, auth=Depends(require_user)):
    """
    Retrieve previously parsed resume by ID.
    """
    db = load_resume_db()
    
    if resume_id not in db:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_data = db[resume_id]

    # Verify user owns this resume
    if resume_data.get("user_id") != str(auth.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "ok": True,
        "data": resume_data
    }

# ============================================================================
# GET /resume – List user's resumes
# ============================================================================
@router.get("")
async def list_resumes(auth=Depends(require_user)):
    """
    List all resumes for the authenticated user.
    """
    user_id = str(auth.id)
    db = load_resume_db()
    
    user_resumes = [
        r for r in db.values()
        if r.get("user_id") == user_id
    ]

    return {
        "ok": True,
        "data": {
            "resumes": user_resumes,
            "count": len(user_resumes)
        }
    }

# ============================================================================
# LEGACY Support
# ============================================================================
@router.post("/parse")
def parse(auth=Depends(require_user)):
    return {
        "ok": False,
        "error": {
            "code": "DEPRECATED",
            "message": "Use POST /resume/upload with file upload instead"
        }
    }

@router.post("/enrich")
def enrich(auth=Depends(require_user)):
    return {
        "ok": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "AI enrichment service coming soon"
        }
    }
