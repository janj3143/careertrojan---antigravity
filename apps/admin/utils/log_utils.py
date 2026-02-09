
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

"""
Log utilities for IntelliCV Admin Portal.
Provides log tailing and latest log file retrieval.
"""
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Optional, List

def get_latest_log_file(logs_dir: Path) -> Optional[Path]:
    if not logs_dir.exists():
        return None
    files: List[Path] = [p for p in logs_dir.iterdir() if p.is_file()]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]

def tail_file(path: Path, max_lines: int = 500) -> str:
    with path.open('r', encoding='utf-8', errors='replace') as f:
        lines = deque(f, maxlen=max_lines)
    return ''.join(lines)

def get_latest_log_content(logs_dir: Path, max_lines: int = 500):
    latest = get_latest_log_file(logs_dir)
    if not latest:
        return {"file": None, "modified": None, "size": 0, "content": ""}
    try:
        content = tail_file(latest, max_lines=max_lines)
        stat = latest.stat()
        return {
            "file": latest.name,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'),
            "size": stat.st_size,
            "content": content,
        }
    except Exception as e:
        return {"error": f"Failed to read log: {e}"}
