from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/api/admin/v1/abuse", tags=["admin-abuse"])

import os
PROJECT_ROOT = Path(os.environ.get("CAREERTROJAN_DATA_ROOT", "L:\\antigravity_version_ai_data_final"))
STORE = PROJECT_ROOT / "resume_store"


@router.get("/queue")
def queue() -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    if not STORE.exists():
        return {"items": []}

    for user_dir in STORE.iterdir():
        if not user_dir.is_dir():
            continue
        for item in user_dir.glob("*.json"):
            try:
                obj = json.loads(item.read_text(encoding="utf-8"))
                if obj.get("status") == "pending":
                    abuse = obj.get("abuse") or {}
                    rows.append({
                        "user_id": obj.get("user_id"),
                        "resume_id": obj.get("resume_id"),
                        "created_at": obj.get("created_at"),
                        "decision": abuse.get("decision"),
                        "risk_score": abuse.get("risk_score"),
                        "reason_codes": abuse.get("reason_codes"),
                    })
            except Exception:
                continue

    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"items": rows[:200]}
