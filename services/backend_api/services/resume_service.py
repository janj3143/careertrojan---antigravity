
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ResumeService:
    """
    Simple file-system based Resume Store for the Runtime.
    Stores uploads in ./data/user_uploads/{user_id}/
    """
    def __init__(self):
        self.base_path = Path("C:/careertrojan/data/user_uploads")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_upload(self, user_id: int, file_obj, filename: str) -> Dict[str, Any]:
        user_dir = self.base_path / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        ext = filename.split('.')[-1] if '.' in filename else 'bin'
        file_id = str(uuid.uuid4())
        save_path = user_dir / f"{file_id}.{ext}"
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        return {
            "resume_id": file_id,
            "filename": filename,
            "path": str(save_path),
            "uploaded_at": datetime.utcnow().isoformat()
        }

    def parse_resume(self, resume_id: str) -> Dict[str, Any]:
        # Mock parser for now
        return {
            "parsed": True,
            "skills": ["Python", "FastAPI", "Leadership"],
            "experience": [{"title": "Software Eng", "company": "Tech Corp"}],
            "raw_text": "Sample resume text..."
        }
