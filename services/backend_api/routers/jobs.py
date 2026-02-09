from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import uuid

router = APIRouter(prefix="/api/jobs/v1", tags=["jobs"])

# In-memory storage for demo purposes
_jobs_db = [
    {
        "id": "job_1",
        "title": "Senior React Developer",
        "company": "TechCorp",
        "location": "Remote",
        "salary_range": "$120k - $150k",
        "posted_at": "2025-11-01"
    },
    {
        "id": "job_2",
        "title": "Python Backend Engineer",
        "company": "DataSystems",
        "location": "New York, NY",
        "salary_range": "$130k - $160k",
        "posted_at": "2025-11-05"
    },
     {
        "id": "job_3",
        "title": "AI Research Scientist",
        "company": "NextGen AI",
        "location": "San Francisco, CA",
        "salary_range": "$180k - $250k",
        "posted_at": "2025-11-10"
    }
]

@router.get("/index")
async def get_job_index():
    """
    Get Job Index (Legacy: 10_Job_Index.py)
    """
    return {"jobs": _jobs_db, "count": len(_jobs_db)}

@router.get("/search")
async def search_jobs(q: str = Query(..., min_length=1)):
    """
    Search jobs by title or company
    """
    results = [
        j for j in _jobs_db 
        if q.lower() in j["title"].lower() or q.lower() in j["company"].lower()
    ]
    return {"jobs": results, "count": len(results)}
