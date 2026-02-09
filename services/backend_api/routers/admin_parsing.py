"""
backend/api/routes/admin_parsing.py

Admin parsing endpoint – batch file processing via thin client.
Bridges React Admin Portal (Page 06) to Universal Parser (port 8010).

Flow:
1. Admin uploads file to /admin/parse
2. Backend forwards to /v1/parse on port 8010
3. Backend stores result with parse_id
4. Returns parse result to React admin dashboard
"""

import httpx
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/admin/v1/parsing", tags=["admin-parsing"])

# In-memory storage for admin parse results (replace with DB in production)
admin_parse_store: dict[str, dict] = {}


from services.backend_api.routers.auth import get_current_active_admin as require_admin


@router.post("/parse")
async def admin_parse_file(
    file: UploadFile = File(...),
    _: bool = Depends(require_admin)
):
    """
    Admin endpoint for batch parsing of files.

    Route mapping: Admin /admin/parse → /v1/parse (port 8010)

    Accepts:
    - POST /admin/parse with file upload

    Returns:
    {
        "ok": true,
        "data": {
            "parse_id": "uuid",
            "filename": "resume.pdf",
            "result": {
                "doc_id": "...",
                "source_filename": "...",
                "detected_type": "PDF",
                "raw_text": "...",
                "parsed_json": {...},
                "ai_json": {...},
                "warnings": [],
                "timings": {...},
                "artifacts": {...}
            }
        }
    }
    """
    try:
        # Read uploaded file
        content = await file.read()

        # Call thin client parser service on port 8010
        async with httpx.AsyncClient(timeout=300) as client:
            files = {"upload": (file.filename, content, file.content_type)}
            response = await client.post(
                "http://127.0.0.1:8010/v1/parse",
                files=files
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Parser service error: {response.text}"
            )

        parse_result = response.json()
        parse_id = str(uuid.uuid4())

        # Store for batch retrieval
        admin_parse_store[parse_id] = {
            "parse_id": parse_id,
            "filename": file.filename or "uploaded_file",
            "result": parse_result
        }

        return {
            "ok": True,
            "data": {
                "parse_id": parse_id,
                "filename": file.filename,
                "result": parse_result
            }
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Parser service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parse failed: {str(e)}"
        )


@router.get("/parse/{parse_id}")
async def get_admin_parse(
    parse_id: str,
    _: bool = Depends(require_admin)
):
    """
    Retrieve previously parsed result by ID.
    """
    if parse_id not in admin_parse_store:
        raise HTTPException(status_code=404, detail="Parse result not found")

    return {
        "ok": True,
        "data": admin_parse_store[parse_id]
    }


@router.get("/parse")
async def list_admin_parses(_: bool = Depends(require_admin)):
    """
    List all parsed files from batch processing.
    """
    return {
        "ok": True,
        "data": {
            "parses": list(admin_parse_store.values()),
            "count": len(admin_parse_store)
        }
    }
