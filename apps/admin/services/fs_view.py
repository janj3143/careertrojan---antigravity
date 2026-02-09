from __future__ import annotations
from pathlib import Path
from shared.env import settings

def safe_join(root: str, rel_path: str) -> Path:
    root_p = Path(root).resolve()
    p = root_p.joinpath(rel_path).resolve()
    if root_p not in p.parents and p != root_p:
        raise ValueError("Path traversal blocked.")
    return p

def list_dir(rel_path: str = "") -> dict:
    root = Path(settings.AI_DATA_ROOT)
    p = safe_join(str(root), rel_path) if rel_path else root
    if not p.exists():
        return {"exists": False, "path": str(p), "items": []}
    items = []
    for child in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        items.append({
            "name": child.name,
            "is_dir": child.is_dir(),
            "size": child.stat().st_size if child.is_file() else None
        })
    return {"exists": True, "path": str(p), "items": items}
