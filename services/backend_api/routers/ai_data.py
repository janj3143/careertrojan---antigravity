"""
Backend API Routes for AI Data from ai_data_final directory

Provides RESTful endpoints for accessing parsed resumes, job descriptions,
companies, job titles, locations, and metadata stored in ai_data_final/
"""

from fastapi import APIRouter, Body, HTTPException, Query
import json
from typing import Dict, Any
import logging

from services.shared.paths import paths as runtime_paths
from services.backend_api.services.email_data_service import (
    build_provider_payload,
    get_email_diagnostics,
    get_email_records,
    get_email_reroute_targets,
    get_email_summary,
    get_email_tracking_records,
    get_email_tracking_summary,
    load_legacy_email_records,
    save_email_tracking_record,
    build_guarded_provider_payload,
)

router = APIRouter(prefix="/api/ai-data/v1", tags=["ai-data"])
logger = logging.getLogger("careertrojan.api.ai_data")

# Canonical paths (handles env values that point to either data root or ai_data_final)
AI_DATA_PATH = runtime_paths.ai_data_final
AUTOMATED_PARSER_PATH = runtime_paths.parser_root
USER_DATA_PATH = runtime_paths.user_data

@router.get("/parsed_resumes")
async def get_parsed_resumes() -> Dict[str, Any]:
    """
    Get all parsed resume data from ai_data_final/parsed_resumes

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    parsed_path = AI_DATA_PATH / "parsed_resumes"
    if not parsed_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Parsed resumes directory not found: {parsed_path}"
        )

    resumes = []
    for json_file in parsed_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                resumes.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(resumes),
        "data": resumes
    }


@router.get("/parsed_resumes/{doc_id}")
async def get_parsed_resume(doc_id: str) -> Dict[str, Any]:
    """
    Get specific parsed resume by doc_id

    Args:
        doc_id: Document ID (filename without .json extension)

    Returns:
        dict: {
            "ok": bool,
            "data": dict
        }
    """
    parsed_path = AI_DATA_PATH / "parsed_resumes" / f"{doc_id}.json"
    if not parsed_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Resume {doc_id} not found"
        )

    try:
        with open(parsed_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {"ok": True, "data": data}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading resume {doc_id}: {str(e)}"
        )


@router.get("/job_descriptions")
async def get_job_descriptions() -> Dict[str, Any]:
    """
    Get all parsed job descriptions from ai_data_final/parsed_job_descriptions

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    jd_path = AI_DATA_PATH / "parsed_job_descriptions"
    if not jd_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Job descriptions directory not found: {jd_path}"
        )

    jobs = []
    for json_file in jd_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(jobs),
        "data": jobs
    }


@router.get("/companies")
async def get_companies() -> Dict[str, Any]:
    """
    Get all company data from ai_data_final/companies

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    company_path = AI_DATA_PATH / "companies"
    if not company_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Companies directory not found: {company_path}"
        )

    companies = []
    for json_file in company_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                companies.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(companies),
        "data": companies
    }


@router.get("/job_titles")
async def get_job_titles() -> Dict[str, Any]:
    """
    Get all job title data from ai_data_final/job_titles

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    jt_path = AI_DATA_PATH / "job_titles"
    if not jt_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Job titles directory not found: {jt_path}"
        )

    titles = []
    for json_file in jt_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                titles.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(titles),
        "data": titles
    }


@router.get("/locations")
async def get_locations() -> Dict[str, Any]:
    """
    Get all location data from ai_data_final/locations

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    loc_path = AI_DATA_PATH / "locations"
    if not loc_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Locations directory not found: {loc_path}"
        )

    locations = []
    for json_file in loc_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                locations.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(locations),
        "data": locations
    }


@router.get("/metadata")
async def get_metadata() -> Dict[str, Any]:
    """
    Get all metadata from ai_data_final/metadata

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    meta_path = AI_DATA_PATH / "metadata"
    if not meta_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Metadata directory not found: {meta_path}"
        )

    metadata = []
    for json_file in meta_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(metadata),
        "data": metadata
    }


@router.get("/normalized")
async def get_normalized_data() -> Dict[str, Any]:
    """
    Get all normalized data from ai_data_final/normalized

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    norm_path = AI_DATA_PATH / "normalized"
    if not norm_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Normalized data directory not found: {norm_path}"
        )

    normalized = []
    for json_file in norm_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                normalized.append(data)
        except Exception as e:
            logger.warning("Error loading %s: %s", json_file, e)
            continue

    return {
        "ok": True,
        "count": len(normalized),
        "data": normalized
    }


@router.get("/email_extracted")
async def get_email_extracted() -> Dict[str, Any]:
    """
    Get all email extracted data from ai_data_final/email_extracted

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    emails = load_legacy_email_records(AI_DATA_PATH)

    return {
        "ok": True,
        "count": len(emails),
        "data": emails
    }


@router.get("/emails")
async def get_emails(
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    domain: str | None = Query(default=None),
    query: str | None = Query(default=None),
    email_type: str | None = Query(default=None),
    trust_tier: str | None = Query(default=None, pattern="^(?i)(a|b|c)$"),
) -> Dict[str, Any]:
    payload = get_email_records(
        AI_DATA_PATH,
        limit=limit,
        offset=offset,
        domain=domain,
        query=query,
        email_type=email_type,
        trust_tier=trust_tier,
    )
    return {"ok": True, **payload}


@router.get("/emails/summary")
async def get_emails_summary() -> Dict[str, Any]:
    payload = get_email_summary(AI_DATA_PATH)
    return {"ok": True, "data": payload}


@router.get("/emails/diagnostics")
async def get_emails_diagnostics() -> Dict[str, Any]:
    payload = get_email_diagnostics(AI_DATA_PATH)
    return {"ok": True, "data": payload}


@router.get("/emails/providers/{provider}")
async def get_emails_provider_payload(
    provider: str,
    limit: int = Query(default=500, ge=1, le=5000),
    domain: str | None = Query(default=None),
    email_type: str | None = Query(default="verified"),
    trust_tier: str | None = Query(default="A", pattern="^(?i)(a|b|c)$"),
) -> Dict[str, Any]:
    try:
        payload = build_provider_payload(
            AI_DATA_PATH,
            provider=provider,
            limit=limit,
            domain=domain,
            email_type=email_type,
            trust_tier=trust_tier,
        )
        return {"ok": True, "data": payload}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/emails/providers/{provider}/guarded-payload")
async def get_guarded_email_provider_payload(
    provider: str,
    limit: int = Query(default=500, ge=1, le=5000),
    domain: str | None = Query(default=None),
    email_type: str | None = Query(default="verified"),
    trust_tier: str | None = Query(default="A"),
    allow_non_tier_a: bool = Query(default=False),
    override_reason: str | None = Query(default=None),
) -> dict:
    try:
        guarded = build_guarded_provider_payload(
            ai_data_path=AI_DATA_PATH,
            provider=provider,
            limit=limit,
            domain=domain,
            email_type=email_type,
            trust_tier=trust_tier,
            allow_non_tier_a=allow_non_tier_a,
            override_reason=override_reason,
        )
        policy = guarded.get("policy") or {}
        if not bool(policy.get("pass", False)):
            raise HTTPException(status_code=400, detail=guarded)
        return guarded
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/emails/tracking")
async def get_emails_tracking(
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    result: str | None = Query(default=None),
) -> Dict[str, Any]:
    payload = get_email_tracking_records(
        AI_DATA_PATH,
        limit=limit,
        offset=offset,
        result=result,
    )
    return {"ok": True, **payload}


@router.get("/emails/tracking/summary")
async def get_emails_tracking_summary() -> Dict[str, Any]:
    payload = get_email_tracking_summary(AI_DATA_PATH)
    return {"ok": True, "data": payload}


@router.get("/emails/tracking/reroute-targets")
async def get_emails_tracking_reroute_targets() -> Dict[str, Any]:
    payload = get_email_reroute_targets(AI_DATA_PATH)
    return {"ok": True, "data": payload}


@router.post("/emails/tracking")
async def create_emails_tracking_record(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    try:
        row = save_email_tracking_record(AI_DATA_PATH, payload)
        return {"ok": True, "data": row}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save email tracking event: {exc}")


@router.get("/status")
async def get_ai_data_status() -> Dict[str, Any]:
    """
    Get status of all ai_data_final directories

    Returns:
        dict: Directory existence and file counts
    """
    directories = [
        "parsed_resumes",
        "parsed_job_descriptions",
        "companies",
        "job_titles",
        "locations",
        "metadata",
        "normalized",
        "email_extracted",
        "emails",
    ]

    status = {}
    for dir_name in directories:
        dir_path = AI_DATA_PATH / dir_name
        if dir_path.exists():
            # Fast count estimate
            count = 0
            try:
                for _ in dir_path.iterdir():
                    count += 1
                    if count >= 50: break
            except: pass
            
            status[dir_name] = {
                "exists": True,
                "file_count": f"{count}+" if count >= 50 else count
            }
        else:
            status[dir_name] = {
                "exists": False,
                "file_count": 0
            }

    return {
        "ok": True,
        "base_path": str(AI_DATA_PATH.absolute()),
        "directories": status
    }


@router.get("/parser/ingestion-status")
async def get_parser_ingestion_status() -> Dict[str, Any]:
    manifest = AI_DATA_PATH / "parsed_from_automated" / "parser_ingestion_status.json"
    summary = AI_DATA_PATH / "parsed_from_automated" / "parser_ingestion_status_summary.json"

    if summary.exists():
        try:
            payload = json.loads(summary.read_text(encoding="utf-8"))
            return {"ok": True, "data": payload}
        except Exception:
            pass

    if manifest.exists():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            return {"ok": True, "data": payload}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Invalid ingestion status manifest: {exc}")

    return {
        "ok": False,
        "detail": "Parser ingestion status manifest not found",
        "expected": [str(summary), str(manifest)],
    }

# --- Automated Parser Endpoints ---

@router.get("/automated/candidates")
async def get_automated_candidates() -> Dict[str, Any]:
    """
    Get all candidate JSONs from automated_parser/ai_data/complete_parsing_output
    """
    target_path = AUTOMATED_PARSER_PATH / "ai_data" / "complete_parsing_output"
    if not target_path.exists():
        return {"ok": False, "count": 0, "error": "Directory not found"}
        
    files = []
    count = 0
    # Use iterdir for performance, avoid building full list
    if target_path.exists():
        for item in target_path.iterdir():
            if count >= 100:
                break
            try:
                if item.is_file() and item.suffix == ".json":
                     if item.stat().st_size > 0:
                         files.append(item.name)
                         count += 1
            except: pass
            
    return {
        "ok": True, 
        "count": count,
        "folder": str(target_path),
        "files_preview": files
    }

# --- User Data Endpoints ---

@router.get("/user_data/files")
async def list_user_data_files() -> Dict[str, Any]:
    """
    List files in USER DATA directory (Non-recursive top level)
    """
    if not USER_DATA_PATH.exists():
        return {"ok": False, "count": 0, "error": "Directory not found"}
        
    file_list = []
    count = 0
    # Iterate top level files only with limit
    for item in USER_DATA_PATH.iterdir():
        if count >= 200:
             break
        try:
            if item.is_file():
                if item.stat().st_size > 0:
                    file_list.append({
                        "name": item.name,
                        "size": item.stat().st_size,
                        "extension": item.suffix
                    })
                    count += 1
        except: continue
            
    return {
        "ok": True,
        "count": count,
        "files": file_list # Already limited
    }
