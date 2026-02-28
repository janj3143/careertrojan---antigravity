from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/jobs/v1", tags=["jobs"])

def _data_source_unavailable():
    raise HTTPException(status_code=503, detail="Job data source not configured")

@router.get("/index")
async def get_job_index():
    """
    Get Job Index (Legacy: 10_Job_Index.py)
    """
    _data_source_unavailable()

@router.get("/search")
async def search_jobs(q: str = Query(..., min_length=1)):
    """
    Search jobs by title or company
    """
    _data_source_unavailable()
