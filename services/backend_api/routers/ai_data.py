"""
Backend API Routes for AI Data from ai_data_final directory

Provides RESTful endpoints for accessing parsed resumes, job descriptions,
companies, job titles, locations, and metadata stored in ai_data_final/
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Any

import os
router = APIRouter(prefix="/api/ai-data/v1", tags=["ai-data"])

# Base path to AI data
_DATA_ROOT = os.environ.get("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
AI_DATA_PATH = Path(_DATA_ROOT) / "ai_data_final"
AUTOMATED_PARSER_PATH = Path(_DATA_ROOT) / "automated_parser"
USER_DATA_PATH = Path(_DATA_ROOT) / "USER DATA"

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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
            print(f"Error loading {json_file}: {e}")
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
    email_path = AI_DATA_PATH / "email_extracted"
    if not email_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Email extracted directory not found: {email_path}"
        )

    emails = []
    for json_file in email_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                emails.append(data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue

    return {
        "ok": True,
        "count": len(emails),
        "data": emails
    }


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
        "email_extracted"
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
