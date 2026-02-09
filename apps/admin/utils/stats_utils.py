"""
System statistics and activity utilities for IntelliCV Admin Portal.
"""
from datetime import datetime
from pathlib import Path
from typing import List

def get_resume_count(data_dir: Path) -> int:
    # Implement based on your data storage (placeholder)
    resumes_dir = data_dir / 'resumes'
    if resumes_dir.exists():
        return len(list(resumes_dir.glob('*.pdf')))
    return 0

def get_daily_processed_count(logs_dir: Path) -> int:
    # Implement based on your logs (placeholder)
    return 0

def get_running_jobs_count() -> int:
    # Implement based on your job tracking (placeholder)
    return 0

def get_last_sync_time() -> str:
    # Implement based on your sync mechanism (placeholder)
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def check_system_health() -> str:
    # Implement health checks (placeholder)
    return "Healthy"

def get_recent_activity(limit: int = 10) -> List[dict]:
    # Implement based on your logging (placeholder)
    return [
        {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'action': 'Resume parsed',
            'details': 'john_doe_resume.pdf',
            'status': 'success'
        }
    ]
