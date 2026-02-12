"""
Backend API Routes for Analytics and Dashboard Data

Provides endpoints for system statistics, dashboard data, and analytics.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import Dict, Any
from datetime import datetime

import os
router = APIRouter(prefix="/api/analytics/v1", tags=["analytics"])

# Source of truth: L: drive → ai_data_final subdirectory
_DATA_ROOT = Path(os.environ.get("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
AI_DATA_PATH = _DATA_ROOT / "ai_data_final"

@router.get("/statistics")
async def get_statistics() -> Dict[str, Any]:
    """
    Get system-wide statistics from ai_data_final directories

    Returns:
        dict: {
            "ok": bool,
            "data": {
                "parsed_resumes": int,
                "job_descriptions": int,
                "companies": int,
                "job_titles": int,
                "locations": int,
                "metadata": int,
                "normalized": int,
                "email_extracted": int
            }
        }
    """
    stats = {}

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

    for dir_name in directories:
        dir_path = AI_DATA_PATH / dir_name
        if dir_path.exists():
            stats[dir_name] = len(list(dir_path.glob("*.json")))
        else:
            stats[dir_name] = 0

    return {
        "ok": True,
        "data": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for admin interface

    Returns:
        dict: {
            "ok": bool,
            "data": {
                "statistics": dict,
                "recent_activity": list,
                "system_status": str,
                "training_status": dict,
                "models": dict
            }
        }
    """
    # Get statistics
    stats_response = await get_statistics()
    stats = stats_response["data"]

    # Get recent resumes
    recent_resumes = []
    resume_path = AI_DATA_PATH / "parsed_resumes"
    if resume_path.exists():
        resume_files = sorted(
            resume_path.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:10]

        for json_file in resume_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recent_resumes.append({
                        "doc_id": json_file.stem,
                        "timestamp": datetime.fromtimestamp(
                            json_file.stat().st_mtime
                        ).isoformat(),
                        "data": data
                    })
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                continue

    # Get training status
    training_status = {
        "active": False,
        "message": "No training in progress"
    }
    status_file = Path("CURRENT_TRAINING_STATUS_REPORT.md")
    if status_file.exists():
        training_status["active"] = True
        training_status["message"] = "Training in progress"

    # Get model count
    models_path = Path("trained_models")
    model_count = 0
    if models_path.exists():
        model_count = len([d for d in models_path.iterdir() if d.is_dir()])

    return {
        "ok": True,
        "data": {
            "statistics": stats,
            "recent_activity": recent_resumes,
            "system_status": "operational",
            "training_status": training_status,
            "models": {
                "count": model_count,
                "available": model_count > 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@router.get("/recent_resumes")
async def get_recent_resumes(limit: int = 10) -> Dict[str, Any]:
    """
    Get most recently added resumes

    Args:
        limit: Maximum number of resumes to return (default 10)

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    resume_path = AI_DATA_PATH / "parsed_resumes"
    if not resume_path.exists():
        return {
            "ok": True,
            "count": 0,
            "data": [],
            "message": "No parsed resumes found"
        }

    resume_files = sorted(
        resume_path.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:limit]

    resumes = []
    for json_file in resume_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                resumes.append({
                    "doc_id": json_file.stem,
                    "timestamp": datetime.fromtimestamp(
                        json_file.stat().st_mtime
                    ).isoformat(),
                    "data": data
                })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue

    return {
        "ok": True,
        "count": len(resumes),
        "data": resumes
    }


@router.get("/recent_jobs")
async def get_recent_jobs(limit: int = 10) -> Dict[str, Any]:
    """
    Get most recently added job descriptions

    Args:
        limit: Maximum number of jobs to return (default 10)

    Returns:
        dict: {
            "ok": bool,
            "count": int,
            "data": List[dict]
        }
    """
    jd_path = AI_DATA_PATH / "parsed_job_descriptions"
    if not jd_path.exists():
        return {
            "ok": True,
            "count": 0,
            "data": [],
            "message": "No parsed job descriptions found"
        }

    job_files = sorted(
        jd_path.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:limit]

    jobs = []
    for json_file in job_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs.append({
                    "doc_id": json_file.stem,
                    "timestamp": datetime.fromtimestamp(
                        json_file.stat().st_mtime
                    ).isoformat(),
                    "data": data
                })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue

    return {
        "ok": True,
        "count": len(jobs),
        "data": jobs
    }


@router.get("/system_health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get comprehensive system health check

    Returns:
        dict: System health indicators
    """
    health = {
        "ai_data_final_exists": AI_DATA_PATH.exists(),
        "backend_operational": True,
        "directories": {},
        "disk_usage": {}
    }

    # Check critical directories
    critical_dirs = [
        "parsed_resumes",
        "parsed_job_descriptions",
        "companies",
        "job_titles"
    ]

    for dir_name in critical_dirs:
        dir_path = AI_DATA_PATH / dir_name
        health["directories"][dir_name] = {
            "exists": dir_path.exists(),
            "file_count": len(list(dir_path.glob("*.json"))) if dir_path.exists() else 0
        }

    # Check trained models
    models_path = Path("trained_models")
    health["trained_models"] = {
        "directory_exists": models_path.exists(),
        "model_count": len([d for d in models_path.iterdir() if d.is_dir()]) if models_path.exists() else 0
    }

    # Overall health status
    all_critical_exist = all(
        health["directories"][d]["exists"]
        for d in critical_dirs
    )

    health["status"] = "healthy" if all_critical_exist else "degraded"
    health["timestamp"] = datetime.utcnow().isoformat()

    return {
        "ok": True,
        "data": health
    }
