"""
Admin Tools API Routes - CaReerTroJan
=====================================
REST API endpoints for admin tools pages:
- File system browser
- Ontology management
- Model registry
- Email analytics
- Evaluation & runs
- Audit logs
- Analytics tools

These are consolidated stubs for the admin portal tools section.
As each tool is implemented fully, endpoints can be moved to dedicated routers.

Author: CareerTrojan System
Date: February 2026
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import os
import logging

from services.backend_api.utils.auth_deps import require_admin

logger = logging.getLogger(__name__)

# Create router - no prefix to handle multiple path patterns
# ALL endpoints in this router require admin authentication
router = APIRouter(tags=["admin-tools"], dependencies=[Depends(require_admin)])


# ============================================================================
# FILE SYSTEM ENDPOINTS (/fs/*) — ADMIN AUTH REQUIRED
# ============================================================================

@router.get("/fs/list")
def list_filesystem(path: str = "/"):
    """
    List files and directories at given path.
    Used by Datasets Browser. Scoped to data roots only.
    """
    import os
    allowed_roots = [
        os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final"),
        os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy"),
    ]
    # Resolve and validate path is under an allowed root
    resolved = os.path.realpath(path)
    if not any(resolved.startswith(os.path.realpath(r)) for r in allowed_roots):
        raise HTTPException(status_code=403, detail="Path outside allowed data roots")
    if not os.path.isdir(resolved):
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    try:
        for entry in sorted(os.scandir(resolved), key=lambda e: e.name):
            stat = entry.stat()
            items.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size if entry.is_file() else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"ok": True, "path": path, "items": items[:500], "total": len(items)}


@router.get("/fs/read")
def read_file_content(path: str):
    """Read file contents. Scoped to allowed data roots."""
    import os
    allowed_roots = [
        os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final"),
        os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy"),
    ]
    resolved = os.path.realpath(path)
    if not any(resolved.startswith(os.path.realpath(r)) for r in allowed_roots):
        raise HTTPException(status_code=403, detail="Path outside allowed data roots")
    if not os.path.isfile(resolved):
        raise HTTPException(status_code=404, detail="File not found")
    stat = os.stat(resolved)
    if stat.st_size > 5 * 1024 * 1024:  # 5 MB limit
        raise HTTPException(status_code=413, detail="File too large (>5MB)")
    try:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "path": path, "content": content, "size": stat.st_size, "encoding": "utf-8"}


# ============================================================================
# ONTOLOGY ENDPOINTS (/ontology/*)
# ============================================================================

@router.get("/ontology/keywords")
def get_keywords(category: Optional[str] = None, limit: int = 200):
    """
    Get keyword ontology from collocation engine gazetteers.
    """
    try:
        from services.ai_engine.collocation_data_loader import get_all_gazetteers
        gaz = get_all_gazetteers()
        keywords = []
        categories_seen = set()
        for cat, info in gaz.get("categories", {}).items():
            if category and cat != category:
                continue
            categories_seen.add(cat)
            for idx, term in enumerate(info.get("sample", []) if limit <= 10 else (info.get("sample", [])[:limit])):
                keywords.append({"id": f"{cat}_{idx}", "term": term, "category": cat, "weight": 1.0, "synonyms": []})
        return {"ok": True, "keywords": keywords[:limit], "categories": sorted(categories_seen), "total": len(keywords)}
    except Exception as exc:
        logger.warning("Collocation engine not available: %s", exc)
        return {"ok": True, "keywords": [], "categories": [], "total": 0, "note": "collocation engine not loaded"}


@router.get("/ontology/phrases")
def get_phrases(limit: int = 200):
    """
    Get known phrases from collocation engine.
    """
    try:
        from services.ai_engine.collocation_engine import collocation_engine as ce
        phrases_list = sorted(ce.known_phrases)[:limit]
        items = [{"id": f"ph_{i}", "pattern": p, "type": "learned", "examples": []} for i, p in enumerate(phrases_list)]
        return {"ok": True, "phrases": items, "types": ["seed", "learned", "gazetteer"], "total": len(ce.known_phrases)}
    except Exception as exc:
        logger.warning("Collocation engine not available: %s", exc)
        return {"ok": True, "phrases": [], "types": [], "total": 0, "note": "collocation engine not loaded"}


# ============================================================================
# MODEL REGISTRY ENDPOINTS (/models/*)
# ============================================================================

@router.get("/models/registry")
def get_model_registry():
    """
    Get AI model registry — discovers trained models on disk + configured LLM providers.
    """
    import os, glob
    models = []
    # 1. Discover trained .pkl / .h5 models from disk
    data_root = os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
    models_dir = os.path.join(data_root, "trained_models")
    if os.path.isdir(models_dir):
        for fp in sorted(glob.glob(os.path.join(models_dir, "*"))):
            name = os.path.basename(fp)
            ext = os.path.splitext(name)[1]
            size_kb = round(os.path.getsize(fp) / 1024, 1)
            models.append({
                "id": name,
                "provider": "local",
                "name": name.replace("_", " ").replace(ext, "").title(),
                "status": "active",
                "format": ext.lstrip("."),
                "size_kb": size_kb,
                "use_cases": [],
            })
    # 2. Configured LLM providers
    if os.getenv("OPENAI_API_KEY"):
        models.append({"id": "gpt-4-turbo", "provider": "openai", "name": "GPT-4 Turbo", "status": "active"})
    if os.getenv("ANTHROPIC_API_KEY"):
        models.append({"id": "claude-3-sonnet", "provider": "anthropic", "name": "Claude 3 Sonnet", "status": "active"})
    return {"ok": True, "models": models, "total": len(models)}


# ============================================================================
# EMAIL ENDPOINTS (/email/*)
# ============================================================================

@router.get("/email/analytics")
def get_email_analytics(days: int = 7):
    """
    Get email sending analytics from DB.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        total = db.execute("SELECT count(*) FROM email_sends WHERE created_at >= :c", {"c": cutoff}).scalar() or 0
        by_status = db.execute(
            "SELECT status, count(*) FROM email_sends WHERE created_at >= :c GROUP BY status", {"c": cutoff}
        ).fetchall()
        stats = {r[0]: r[1] for r in by_status} if by_status else {}
        daily = []
        for i in range(days):
            d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            cnt = db.execute(
                "SELECT count(*) FROM email_sends WHERE created_at::date = :d", {"d": d}
            ).scalar() or 0
            daily.append({"date": d, "sent": cnt})
        sent = stats.get("sent", 0) + stats.get("delivered", 0) + stats.get("pending", 0)
        return {"ok": True, "period": f"{days}d", "stats": stats, "total_sent": total, "daily": daily}
    except Exception as exc:
        logger.warning("email analytics query failed: %s", exc)
        return {"ok": True, "period": f"{days}d", "stats": {}, "total_sent": 0, "daily": [], "note": "email_sends table not available"}
    finally:
        db.close()


@router.get("/email/captured")
def get_captured_emails():
    """
    Get captured/queued emails for review.
    Used by Email Capture page.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        # Query email_campaigns or email_queue table for recent sends
        rows = db.execute(
            """SELECT id, recipient_email, subject, status, created_at
               FROM email_sends ORDER BY created_at DESC LIMIT 50"""
        ).fetchall()
        emails = [
            {
                "id": str(r[0]),
                "to": r[1],
                "subject": r[2],
                "status": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ] if rows else []
        return {
            "ok": True,
            "emails": emails,
            "total": len(emails),
            "pending_count": sum(1 for e in emails if e["status"] == "pending"),
        }
    except Exception as exc:
        logger.warning("email_sends table not available yet: %s", exc)
        return {"ok": True, "emails": [], "total": 0, "pending_count": 0}
    finally:
        db.close()


# ============================================================================
# EVALUATION ENDPOINTS (/eval/*)
# ============================================================================

@router.get("/eval/runs")
def get_evaluation_runs(limit: int = 50):
    """
    Get AI evaluation runs from control plane evaluation history.
    """
    try:
        from services.ai_engine.control_plane.evaluation import EvaluationPipeline
        ep = EvaluationPipeline()
        history = getattr(ep, "history", [])[-limit:]
        runs = []
        for i, entry in enumerate(reversed(history)):
            runs.append({
                "id": f"eval_{i:03d}",
                "name": entry.get("test_name", "unnamed"),
                "status": "completed" if entry.get("passed") else "failed",
                "started_at": entry.get("timestamp"),
                "completed_at": entry.get("completed_at"),
                "metrics": entry.get("metrics", {}),
            })
        return {"ok": True, "runs": runs, "total": len(runs)}
    except Exception as exc:
        logger.warning("Evaluation history not available: %s", exc)
        return {"ok": True, "runs": [], "total": 0, "note": "evaluation pipeline not available"}


# ============================================================================
# PROCESSING RUNS ENDPOINTS (/runs/*)
# ============================================================================

@router.get("/runs/parser")
def get_parser_runs(limit: int = 50):
    """
    Get parser processing runs from interaction logs.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, session_id, status_code, response_time_ms, created_at
               FROM interactions WHERE action_type = 'cv_upload'
               ORDER BY created_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        runs = []
        for r in (rows or []):
            runs.append({
                "id": f"run_p{r[0]}",
                "type": "single",
                "status": "completed" if r[2] and r[2] < 400 else "failed",
                "processed": 1,
                "errors": 0 if r[2] and r[2] < 400 else 1,
                "started_at": r[4].isoformat() if r[4] else None,
                "duration_sec": round(r[3] / 1000, 2) if r[3] else 0,
            })
        return {"ok": True, "runs": runs, "total": len(runs)}
    except Exception as exc:
        logger.warning("parser runs query failed: %s", exc)
        return {"ok": True, "runs": [], "total": 0, "note": "interactions table not available"}
    finally:
        db.close()


@router.get("/runs/enrichment")
def get_enrichment_runs(limit: int = 50):
    """
    Get AI enrichment processing runs from interaction logs.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, session_id, status_code, response_time_ms, metadata_json, created_at
               FROM interactions WHERE action_type IN ('enrichment', 'ai_enrichment', 'skill_extraction')
               ORDER BY created_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        runs = []
        for r in (rows or []):
            runs.append({
                "id": f"run_e{r[0]}",
                "type": "enrichment",
                "status": "completed" if r[2] and r[2] < 400 else "failed",
                "items": 1,
                "started_at": r[5].isoformat() if r[5] else None,
                "duration_sec": round(r[3] / 1000, 2) if r[3] else 0,
            })
        return {"ok": True, "runs": runs, "total": len(runs)}
    except Exception as exc:
        logger.warning("enrichment runs query failed: %s", exc)
        return {"ok": True, "runs": [], "total": 0, "note": "interactions table not available"}
    finally:
        db.close()


# ============================================================================
# PROMPTS REGISTRY ENDPOINTS (/prompts/*)
# ============================================================================

@router.get("/prompts/registry")
def get_prompts_registry():
    """
    Get prompt templates — discovers .py inference modules with system_prompt strings.
    """
    import os, glob
    prompts = []
    ai_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "workers", "ai", "ai-workers", "inference")
    ai_root = os.path.normpath(ai_root)
    if os.path.isdir(ai_root):
        for fp in sorted(glob.glob(os.path.join(ai_root, "*.py"))):
            name = os.path.basename(fp).replace(".py", "").replace("_", " ").title()
            stat = os.stat(fp)
            prompts.append({
                "id": os.path.basename(fp),
                "name": name,
                "version": "1.0",
                "model": "varies",
                "category": "inference",
                "last_updated": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    # Also check training scripts
    train_root = os.path.join(os.path.dirname(ai_root), "training")
    if os.path.isdir(train_root):
        for fp in sorted(glob.glob(os.path.join(train_root, "*.py"))):
            name = os.path.basename(fp).replace(".py", "").replace("_", " ").title()
            stat = os.stat(fp)
            prompts.append({
                "id": os.path.basename(fp),
                "name": name,
                "version": "1.0",
                "model": "varies",
                "category": "training",
                "last_updated": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    categories = sorted(set(p["category"] for p in prompts))
    return {"ok": True, "prompts": prompts, "categories": categories, "total": len(prompts)}


# ============================================================================
# AUDIT ENDPOINTS (/audit/*)
# ============================================================================

@router.get("/audit/admin")
def get_admin_audit_log(limit: int = 50):
    """
    Get admin action audit log from DB.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, actor_id, action, resource_type, resource_id, detail, ip_address, created_at
               FROM audit_log WHERE actor_id IS NOT NULL
               ORDER BY created_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        events = []
        for r in (rows or []):
            events.append({
                "id": f"aud_{r[0]}",
                "admin_id": str(r[1]) if r[1] else None,
                "action": r[2],
                "target": f"{r[3]}:{r[4]}" if r[3] else r[4],
                "detail": r[5],
                "ip": r[6],
                "timestamp": r[7].isoformat() if r[7] else None,
            })
        return {"ok": True, "events": events, "total": len(events)}
    except Exception as exc:
        logger.warning("audit_log query failed: %s", exc)
        return {"ok": True, "events": [], "total": 0, "note": "audit_log table not available"}
    finally:
        db.close()


@router.get("/audit/users")
def get_user_audit_log(limit: int = 50):
    """
    Get user activity audit log from interactions table.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, user_id, action_type, path, status_code, created_at
               FROM interactions WHERE user_id IS NOT NULL
               ORDER BY created_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        events = []
        for r in (rows or []):
            events.append({
                "id": f"ua_{r[0]}",
                "user_id": str(r[1]) if r[1] else None,
                "action": r[2] or "request",
                "details": r[3] or "",
                "status_code": r[4],
                "timestamp": r[5].isoformat() if r[5] else None,
            })
        return {"ok": True, "events": events, "total": len(events)}
    except Exception as exc:
        logger.warning("interactions query failed: %s", exc)
        return {"ok": True, "events": [], "total": 0, "note": "interactions table not available"}
    finally:
        db.close()


# ============================================================================
# ANALYTICS ENDPOINTS (/analytics/*)
# ============================================================================

@router.get("/analytics/fairness")
def get_fairness_analytics():
    """
    Get bias and fairness metrics from drift detection module.
    """
    try:
        from services.ai_engine.control_plane.drift import DriftDetector
        dd = DriftDetector()
        report = dd.get_latest_report() if hasattr(dd, "get_latest_report") else {}
        return {
            "ok": True,
            "metrics": report.get("fairness", {}),
            "by_dimension": report.get("dimensions", {}),
            "recommendations": report.get("recommendations", []),
            "source": "drift_detector",
        }
    except Exception as exc:
        logger.warning("fairness analytics not available: %s", exc)
        return {"ok": True, "metrics": {}, "by_dimension": {}, "recommendations": [], "note": "drift detector not available"}


@router.get("/analytics/scoring")
def get_scoring_analytics():
    """
    Get resume scoring distribution from calibration module.
    """
    try:
        from services.ai_engine.control_plane.calibration import ConfidenceCalibrator
        cal = ConfidenceCalibrator()
        stats = cal.get_calibration_stats() if hasattr(cal, "get_calibration_stats") else {}
        return {
            "ok": True,
            "distribution": stats.get("distribution", {}),
            "average_score": stats.get("mean", 0),
            "median_score": stats.get("median", 0),
            "total_samples": stats.get("total_samples", 0),
            "source": "calibration_module",
        }
    except Exception as exc:
        logger.warning("scoring analytics not available: %s", exc)
        return {"ok": True, "distribution": {}, "average_score": 0, "median_score": 0, "note": "calibration module not available"}


# ============================================================================
# ADMIN TOOL SPECIFIC ENDPOINTS (/admin/*)
# ============================================================================

@router.get("/admin/about")
def get_admin_about():
    """
    Get system about information.
    Used by About page in tools section.
    """
    return {
        "ok": True,
        "name": "CareerTrojan Admin",
        "version": "1.0.0",
        "build": "2026.02.10",
        "environment": os.getenv("CAREERTROJAN_ENV", "development"),
        "api_version": "v1",
        "features": [
            "User Management",
            "System Monitoring",
            "AI Model Registry",
            "Resume Parser Management",
            "Compliance & GDPR Tools"
        ]
    }


@router.get("/admin/backup")
def get_admin_backup():
    """
    Get backup status — scans backup directory.
    """
    import os
    backup_dir = os.getenv("CAREERTROJAN_BACKUP_DIR", "/backups/careertrojan")
    if not os.path.isdir(backup_dir):
        return {"ok": True, "last_backup": None, "backup_location": backup_dir, "backups": [], "note": "backup directory not found"}
    backups = []
    for entry in sorted(os.scandir(backup_dir), key=lambda e: e.stat().st_mtime, reverse=True)[:20]:
        stat = entry.stat()
        backups.append({
            "name": entry.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 1),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {
        "ok": True,
        "backup_location": backup_dir,
        "last_backup": backups[0]["created_at"] if backups else None,
        "backups": backups,
        "total": len(backups),
    }


@router.get("/admin/data-health")
def get_data_health():
    """
    Get data roots health status — live filesystem scan.
    """
    import os
    roots_config = [
        (os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final"), "ai_data"),
        (os.getenv("CAREERTROJAN_USER_DATA", "/data/user_uploads"), "user_uploads"),
        (os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy"), "working"),
    ]
    roots = []
    for root_path, label in roots_config:
        entry = {"path": root_path, "label": label}
        if not os.path.isdir(root_path):
            entry.update({"status": "missing", "size_gb": 0, "files": 0})
        else:
            total_size = 0
            file_count = 0
            try:
                for dirpath, _dirs, files in os.walk(root_path):
                    for f in files:
                        fp = os.path.join(dirpath, f)
                        try:
                            total_size += os.path.getsize(fp)
                            file_count += 1
                        except OSError:
                            pass
            except Exception:
                pass
            entry.update({
                "status": "healthy",
                "size_gb": round(total_size / (1024 ** 3), 2),
                "files": file_count,
                "last_scan": datetime.utcnow().isoformat(),
            })
        roots.append(entry)
    return {"ok": True, "roots": roots}


@router.get("/admin/diagnostics")
def get_admin_diagnostics():
    """
    Get live system diagnostics.
    """
    import platform, sys, os
    # Memory via psutil if available
    mem_info = {}
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_info = {
            "total_mb": round(mem.total / (1024**2)),
            "used_mb": round(mem.used / (1024**2)),
            "available_mb": round(mem.available / (1024**2)),
        }
    except ImportError:
        mem_info = {"note": "psutil not installed"}

    # DB check
    db_status = "unknown"
    try:
        from services.backend_api.db.connection import SessionLocal
        sess = SessionLocal()
        sess.execute("SELECT 1")
        db_status = "healthy"
        sess.close()
    except Exception as exc:
        db_status = f"error: {exc}"

    # Redis check
    cache_status = "unknown"
    try:
        from services.backend_api.db.connection import redis_client
        redis_client.ping()
        cache_status = "healthy"
    except Exception as exc:
        cache_status = f"error: {exc}"

    return {
        "ok": True,
        "system": {
            "os": platform.system(),
            "platform": platform.platform(),
            "python": sys.version,
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
        },
        "memory": mem_info,
        "services": {"database": db_status, "cache": cache_status},
    }


@router.get("/admin/api-explorer")
def get_admin_api_explorer():
    """
    Get API explorer data — live from OpenAPI schema.
    """
    try:
        from services.backend_api.main import app
        total = 0
        by_tag: Dict[str, int] = {}
        for route in getattr(app, "routes", []):
            methods = getattr(route, "methods", set())
            if not methods:
                continue
            tags = getattr(route, "tags", []) or ["untagged"]
            for tag in tags:
                by_tag[tag] = by_tag.get(tag, 0) + len(methods)
            total += len(methods)
        return {
            "ok": True,
            "openapi_url": "/openapi.json",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "total_endpoints": total,
            "by_category": by_tag,
        }
    except Exception as exc:
        logger.warning("api-explorer introspection failed: %s", exc)
        return {"ok": True, "openapi_url": "/openapi.json", "docs_url": "/docs", "redoc_url": "/redoc", "total_endpoints": 0, "by_category": {}}


@router.get("/admin/exports")
def get_admin_exports(limit: int = 50):
    """
    Get export jobs from DataExportRequest table.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, user_id, status, file_path, requested_at, completed_at
               FROM data_export_requests ORDER BY requested_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        exports = []
        for r in (rows or []):
            size_kb = 0
            if r[3]:
                try:
                    size_kb = round(os.path.getsize(r[3]) / 1024, 1)
                except OSError:
                    pass
            exports.append({
                "id": str(r[0]),
                "user_id": str(r[1]) if r[1] else None,
                "status": r[2],
                "file_path": r[3],
                "size_kb": size_kb,
                "requested_at": r[4].isoformat() if r[4] else None,
                "completed_at": r[5].isoformat() if r[5] else None,
            })
        return {"ok": True, "exports": exports, "total": len(exports)}
    except Exception as exc:
        logger.warning("data_export_requests query failed: %s", exc)
        return {"ok": True, "exports": [], "total": 0, "note": "data_export_requests table not available"}
    finally:
        db.close()


@router.get("/admin/logs-viewer")
def get_admin_logs(level: str = "all", limit: int = 100):
    """
    Get system logs from log file — real log reader.
    """
    import os, json as _json
    log_path = os.getenv("CAREERTROJAN_LOG_FILE", "/app/logs/backend.log")
    logs = []
    levels_seen = set()
    try:
        if os.path.isfile(log_path):
            with open(log_path, "r") as f:
                tail_lines = f.readlines()[-limit * 2:]
            for line in tail_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = _json.loads(line)
                except _json.JSONDecodeError:
                    entry = {"timestamp": "", "level": "INFO", "service": "backend", "message": line}
                entry_level = entry.get("level", "INFO").upper()
                levels_seen.add(entry_level)
                if level != "all" and entry_level != level.upper():
                    continue
                logs.append(entry)
    except Exception as exc:
        logger.warning("Could not read log file %s: %s", log_path, exc)

    return {
        "ok": True,
        "logs": logs[-limit:],
        "levels": sorted(levels_seen) if levels_seen else ["DEBUG", "INFO", "WARN", "ERROR"],
        "services": ["backend"],
        "total": len(logs),
    }


@router.get("/admin/notifications")
def get_admin_notifications(limit: int = 20):
    """
    Get admin notifications from recent audit log events.
    """
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        rows = db.execute(
            """SELECT id, action, resource_type, detail, created_at
               FROM audit_log ORDER BY created_at DESC LIMIT :lim""",
            {"lim": limit},
        ).fetchall()
        notifications = []
        for r in (rows or []):
            ntype = "info"
            action = r[1] or ""
            if "delete" in action or "error" in action:
                ntype = "warning"
            elif "export" in action or "complete" in action:
                ntype = "success"
            notifications.append({
                "id": f"n{r[0]}",
                "type": ntype,
                "title": action.replace("_", " ").title(),
                "message": r[3] or f"{r[2] or ''} {action}",
                "read": True,
                "created_at": r[4].isoformat() if r[4] else None,
            })
        return {"ok": True, "notifications": notifications, "unread_count": 0}
    except Exception as exc:
        logger.warning("notifications query failed: %s", exc)
        return {"ok": True, "notifications": [], "unread_count": 0, "note": "audit_log table not available"}
    finally:
        db.close()


@router.get("/admin/resume-viewer")
def get_resume_viewer_data(resume_id: Optional[str] = None):
    """
    Get resume JSON data for viewer. Fetches from DB if resume_id given.
    """
    if not resume_id:
        return {"ok": True, "sample_resume": None, "message": "Provide ?resume_id= to load a resume"}
    try:
        from services.backend_api.db.connection import get_db
        db = next(get_db())
        row = db.execute(
            "SELECT id, user_id, parsed_json, created_at FROM resumes WHERE id = :rid",
            {"rid": resume_id},
        ).fetchone()
        db.close()
        if not row:
            raise HTTPException(status_code=404, detail="Resume not found")
        import json as _json
        parsed = _json.loads(row[2]) if row[2] else {}
        return {"ok": True, "sample_resume": parsed, "resume_id": str(row[0]), "user_id": str(row[1])}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Resume viewer query failed: %s", exc)
        return {"ok": False, "error": str(exc)}


@router.get("/admin/route-map")
def get_admin_route_map():
    """
    Get live route map from FastAPI app object.
    """
    try:
        from services.backend_api.main import app
        by_tag: Dict[str, int] = {}
        total = 0
        for route in getattr(app, "routes", []):
            methods = getattr(route, "methods", set())
            if not methods:
                continue
            tags = getattr(route, "tags", []) or ["untagged"]
            for tag in tags:
                by_tag[tag] = by_tag.get(tag, 0) + len(methods)
            total += len(methods)
        return {"ok": True, "routes": by_tag, "total": total}
    except Exception as exc:
        logger.warning("route-map introspection failed: %s", exc)
        return {"ok": True, "routes": {}, "total": 0, "note": "could not introspect app"}


@router.get("/admin/config")
def get_admin_config():
    """
    Get system configuration.
    Used by System Config page in tools section.
    """
    return {
        "ok": True,
        "config": {
            "app_name": "CareerTrojan",
            "environment": os.getenv("CAREERTROJAN_ENV", "development"),
            "debug": os.getenv("CAREERTROJAN_DEBUG", "false") == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "max_upload_size_mb": 10,
            "session_timeout_minutes": 60,
            "ai_provider": os.getenv("AI_PROVIDER", "openai"),
            "features": {
                "payments": True,
                "mentorship": True,
                "coaching": True,
                "job_matching": True
            }
        }
    }
