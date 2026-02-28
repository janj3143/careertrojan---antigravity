"""Admin token configuration and analytics endpoints."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from services.backend_api.routers.admin import require_admin
from services.shared.paths import CareerTrojanPaths

try:
    from services.backend_api.routers import payment
except Exception:
    payment = None

try:
    from services.backend_api.services.credit_system import ACTION_COSTS
except Exception:
    ACTION_COSTS = {}

router = APIRouter(tags=["admin-tokens"])

PLAN_KEYS = ("free", "monthly", "annual", "elitepro")
_LOCK = threading.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _store_file() -> Path:
    env_path = os.getenv("CAREERTROJAN_TOKEN_STORE")
    if env_path:
        return Path(env_path)
    return CareerTrojanPaths().app_root / "data" / "token_admin_store.json"


def _default_plans() -> Dict[str, Dict[str, Any]]:
    default = {
        "free": {"included_tokens_per_month": 50, "soft_limit_pct": 80, "hard_limit_pct": 100, "overage_price_per_1k": None},
        "monthly": {"included_tokens_per_month": 500, "soft_limit_pct": 80, "hard_limit_pct": 100, "overage_price_per_1k": 0.05},
        "annual": {"included_tokens_per_month": 1000, "soft_limit_pct": 80, "hard_limit_pct": 100, "overage_price_per_1k": 0.04},
        "elitepro": {"included_tokens_per_month": 5000, "soft_limit_pct": 80, "hard_limit_pct": 100, "overage_price_per_1k": 0.03},
    }
    if payment is None:
        return default

    plans = dict(default)
    for key in PLAN_KEYS:
        plan = payment.PLANS.get(key)
        if not plan:
            continue
        plans[key]["included_tokens_per_month"] = int(plan.get("token_limit", plans[key]["included_tokens_per_month"]))
    return plans


def _default_costs() -> List[Dict[str, Any]]:
    now = _iso(_utcnow())
    rows: List[Dict[str, Any]] = []
    for action_id, cost in ACTION_COSTS.items():
        rows.append(
            {
                "feature": action_id,
                "tokens": int(getattr(cost, "credits", 0)),
                "updated_at": now,
                "updated_by": "system",
            }
        )
    return rows


def _default_store() -> Dict[str, Any]:
    return {
        "plans": _default_plans(),
        "usage_rows": [],
        "costs": _default_costs(),
        "ledger": [],
        "subscriptions": [],
    }


def _load_store() -> Dict[str, Any]:
    with _LOCK:
        path = _store_file()
        if not path.exists():
            store = _default_store()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(store, indent=2), encoding="utf-8")
            return store

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = _default_store()

        for key, value in _default_store().items():
            data.setdefault(key, value)

        return data


def _save_store(store: Dict[str, Any]) -> None:
    with _LOCK:
        path = _store_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _require_plans(store: Dict[str, Any]) -> Dict[str, Any]:
    plans = store.get("plans")
    if not isinstance(plans, dict):
        raise HTTPException(status_code=500, detail="Token plans storage is invalid.")

    missing = [k for k in PLAN_KEYS if k not in plans]
    if missing:
        raise HTTPException(status_code=500, detail=f"Token plans missing required keys: {missing}")
    return plans


def _subscriptions_from_payment() -> List[Dict[str, Any]]:
    if payment is None:
        return []

    subs = []
    now = _utcnow()
    for user_id, record in payment._user_subscriptions.items():
        if not isinstance(record, dict):
            continue
        plan = str(record.get("plan_id") or "free")
        started = record.get("started_at")
        next_billing = record.get("next_billing")
        cancelled = bool(record.get("cancelled", False))

        status = "active"
        if cancelled:
            status = "cancelled"
        elif next_billing:
            try:
                nb = datetime.fromisoformat(next_billing.replace("Z", "+00:00"))
                if nb < now:
                    status = "expired"
            except Exception:
                pass

        subs.append(
            {
                "user_id": user_id,
                "plan": plan,
                "status": status,
                "started_at": started,
                "next_billing": next_billing,
                "subscription_id": record.get("subscription_id"),
            }
        )
    return subs


def _get_subscriptions(store: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = _subscriptions_from_payment()
    if rows:
        store["subscriptions"] = rows
        _save_store(store)
        return rows

    subscriptions = store.get("subscriptions")
    if isinstance(subscriptions, list):
        return subscriptions
    return []


def _build_usage_rows(store: Dict[str, Any], month: Optional[str]) -> List[Dict[str, Any]]:
    rows = store.get("usage_rows")
    if isinstance(rows, list) and rows:
        if month:
            return [r for r in rows if str(r.get("month")) == month]
        return rows

    subscriptions = _get_subscriptions(store)
    counts = {k: 0 for k in PLAN_KEYS}
    for s in subscriptions:
        plan = s.get("plan")
        if plan in counts:
            counts[plan] += 1

    generated = []
    current_month = month or _utcnow().strftime("%Y-%m")
    for plan, count in counts.items():
        generated.append(
            {
                "org_id": f"plan-{plan}",
                "org_name": f"{plan.title()} Cohort",
                "plan": plan,
                "active_users": count,
                "tokens_used": 0,
                "tokens_included": int(_require_plans(store)[plan].get("included_tokens_per_month", 0)) * max(count, 1),
                "usage_pct": 0,
                "month": current_month,
            }
        )
    return generated


def _build_kpis(store: Dict[str, Any], days: int) -> Dict[str, Any]:
    ledger = store.get("ledger")
    if not isinstance(ledger, list):
        ledger = []

    cutoff = _utcnow() - timedelta(days=days)
    window = []
    for row in ledger:
        ts = row.get("timestamp")
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if dt >= cutoff:
                window.append(row)
        except Exception:
            continue

    tokens_total = sum(int(r.get("tokens", 0)) for r in window)
    users = {str(r.get("user_id")) for r in window if r.get("user_id")}
    today = _utcnow().date().isoformat()
    tokens_today = sum(int(r.get("tokens", 0)) for r in window if str(r.get("timestamp", "")).startswith(today))
    avg_tokens_per_user = round(tokens_total / max(len(users), 1), 2)

    return {
        "active_users_30d": len(users),
        "tokens_today": tokens_today,
        "revenue_today": 0,
        "avg_tokens_per_user_30d": avg_tokens_per_user,
    }


def _build_timeseries(store: Dict[str, Any], days: int) -> List[Dict[str, Any]]:
    ledger = store.get("ledger")
    if not isinstance(ledger, list):
        return []

    daily: Dict[str, Dict[str, Any]] = {}
    cutoff = _utcnow().date() - timedelta(days=days - 1)

    for row in ledger:
        ts = str(row.get("timestamp") or "")
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        except Exception:
            continue
        if d < cutoff:
            continue
        key = d.isoformat()
        bucket = daily.setdefault(key, {"date": key, "tokens": 0, "revenue": 0, "users": set()})
        bucket["tokens"] += int(row.get("tokens", 0))
        if row.get("user_id"):
            bucket["users"].add(str(row.get("user_id")))

    rows = []
    for key in sorted(daily.keys()):
        item = daily[key]
        rows.append(
            {
                "date": key,
                "tokens": item["tokens"],
                "active_users": len(item["users"]),
                "revenue": item["revenue"],
            }
        )
    return rows


@router.get("/admin/tokens/plans")
@router.get("/admin/tokens/config")
@router.get("/api/admin/v1/tokens/config")
async def get_token_config(_: bool = Depends(require_admin)) -> Dict[str, Any]:
    store = _load_store()
    plans = _require_plans(store)
    return {"plans": plans, "as_of": _iso(_utcnow())}


@router.post("/admin/tokens/plans")
@router.put("/admin/tokens/plans")
@router.put("/api/admin/v1/tokens/config")
async def put_token_config(payload: Dict[str, Any], _: bool = Depends(require_admin)) -> Dict[str, Any]:
    plans = payload.get("plans")
    if not isinstance(plans, dict) or not plans:
        raise HTTPException(status_code=400, detail="Payload must include non-empty 'plans' dict.")

    missing = [k for k in PLAN_KEYS if k not in plans]
    extra = [k for k in plans if k not in PLAN_KEYS]
    if missing:
        raise HTTPException(status_code=400, detail=f"Plans missing required keys: {missing}")
    if extra:
        raise HTTPException(status_code=400, detail=f"Plans include unknown keys: {extra}")

    for key, cfg in plans.items():
        included = int(cfg.get("included_tokens_per_month", 0))
        if included < 0:
            raise HTTPException(status_code=400, detail=f"{key}.included_tokens_per_month must be >= 0")

    store = _load_store()
    store["plans"] = plans
    _save_store(store)
    return {"plans": store["plans"], "saved_at": _iso(_utcnow())}


@router.get("/admin/tokens/usage")
@router.get("/api/admin/v1/tokens/usage")
async def get_token_usage(month: Optional[str] = None, _: bool = Depends(require_admin)) -> Dict[str, Any]:
    store = _load_store()
    _require_plans(store)
    rows = _build_usage_rows(store, month)
    return {"orgs": rows, "month": month or "current"}


@router.get("/admin/subscriptions")
@router.get("/admin/tokens/subscriptions")
async def get_subscriptions(_: bool = Depends(require_admin)) -> Dict[str, Any]:
    store = _load_store()
    rows = _get_subscriptions(store)
    return {"subscriptions": rows, "as_of": _iso(_utcnow())}


@router.get("/admin/tokens/costs")
async def get_token_costs(_: bool = Depends(require_admin)) -> Dict[str, Any]:
    store = _load_store()
    costs = store.get("costs")
    if not isinstance(costs, list):
        costs = []
    return {"costs": costs, "as_of": _iso(_utcnow())}


@router.post("/admin/tokens/costs/update")
@router.put("/admin/tokens/costs/{feature}")
async def update_token_cost(
    payload: Dict[str, Any],
    feature: Optional[str] = None,
    _: bool = Depends(require_admin),
) -> Dict[str, Any]:
    feature_name = feature or payload.get("feature")
    if not feature_name or not str(feature_name).strip():
        raise HTTPException(status_code=400, detail="feature is required")

    tokens = payload.get("tokens")
    if tokens is None:
        raise HTTPException(status_code=400, detail="tokens is required")
    tokens = int(tokens)
    if tokens < 0:
        raise HTTPException(status_code=400, detail="tokens must be >= 0")

    store = _load_store()
    costs = store.get("costs")
    if not isinstance(costs, list):
        costs = []

    updated_cost = None
    now = _iso(_utcnow())
    for row in costs:
        if row.get("feature") == feature_name:
            row["tokens"] = tokens
            row["updated_at"] = now
            row["updated_by"] = "admin"
            updated_cost = row
            break

    if updated_cost is None:
        updated_cost = {
            "feature": feature_name,
            "tokens": tokens,
            "updated_at": now,
            "updated_by": "admin",
        }
        costs.append(updated_cost)

    store["costs"] = costs
    _save_store(store)
    return {"cost": updated_cost, "saved_at": now}


@router.get("/admin/tokens/logs")
async def get_usage_logs(days: int = 14, _: bool = Depends(require_admin)) -> Dict[str, Any]:
    days = max(1, min(days, 365))
    store = _load_store()
    ledger = store.get("ledger")
    if not isinstance(ledger, list):
        ledger = []

    cutoff = _utcnow() - timedelta(days=days)
    rows: List[Dict[str, Any]] = []
    for row in ledger:
        try:
            ts = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
        except Exception:
            continue
        if ts >= cutoff:
            rows.append(row)

    rows.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return {"logs": rows, "days": days}


@router.get("/admin/tokens/analytics")
async def get_usage_analytics(days: int = 30, _: bool = Depends(require_admin)) -> Dict[str, Any]:
    days = max(1, min(days, 365))
    store = _load_store()
    return {
        "kpis": _build_kpis(store, days),
        "timeseries": _build_timeseries(store, days),
        "days": days,
    }


@router.get("/admin/tokens/ledger/{user_id}")
async def get_user_token_ledger(user_id: str, _: bool = Depends(require_admin)) -> Dict[str, Any]:
    store = _load_store()
    ledger = store.get("ledger")
    if not isinstance(ledger, list):
        ledger = []

    entries = [r for r in ledger if str(r.get("user_id")) == user_id]
    consumed = sum(int(r.get("tokens", 0)) for r in entries if int(r.get("tokens", 0)) > 0)
    entries.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

    return {
        "user_id": user_id,
        "entries": entries,
        "summary": {
            "events": len(entries),
            "tokens_consumed": consumed,
        },
    }


@router.get("/admin/tokens/unit-economics")
async def get_token_unit_economics(window_days: int = 30, _: bool = Depends(require_admin)) -> Dict[str, Any]:
    window_days = max(1, min(window_days, 365))
    store = _load_store()
    plans = _require_plans(store)
    subs = _get_subscriptions(store)
    price_map = {}
    if payment is not None:
        for key in PLAN_KEYS:
            p = payment.PLANS.get(key)
            if p:
                price_map[key] = float(p.get("price", 0.0))

    avg_cost_per_token_gbp = float(os.getenv("TOKEN_COST_PER_TOKEN_GBP") or "0.0008")
    api_cost_breakdown = [
        {
            "provider": "openai",
            "cost_gbp": round(avg_cost_per_token_gbp * 100000, 2),
            "share_pct": 70,
        },
        {
            "provider": "infrastructure",
            "cost_gbp": round(avg_cost_per_token_gbp * 40000, 2),
            "share_pct": 30,
        },
    ]

    plan_user_counts = {k: 0 for k in PLAN_KEYS}
    for sub in subs:
        plan = sub.get("plan")
        if plan in plan_user_counts and sub.get("status") == "active":
            plan_user_counts[plan] += 1

    plan_rows = []
    for key in PLAN_KEYS:
        included = int(plans[key].get("included_tokens_per_month", 0))
        subscribers = plan_user_counts[key]
        revenue = round(price_map.get(key, 0.0) * subscribers, 2)
        estimated_cost = round(included * subscribers * avg_cost_per_token_gbp, 2)
        gross_margin = round(revenue - estimated_cost, 2)
        margin_pct = round((gross_margin / revenue) * 100, 2) if revenue > 0 else 0.0
        plan_rows.append(
            {
                "plan": key,
                "subscribers": subscribers,
                "included_tokens_per_month": included,
                "price_gbp": price_map.get(key, 0.0),
                "estimated_api_cost_gbp": estimated_cost,
                "estimated_revenue_gbp": revenue,
                "gross_margin_gbp": gross_margin,
                "margin_pct": margin_pct,
            }
        )

    return {
        "assumptions": {
            "window_days": window_days,
            "avg_cost_per_token_gbp": avg_cost_per_token_gbp,
            "generated_at": _iso(_utcnow()),
        },
        "plans": plan_rows,
        "api_cost_breakdown": api_cost_breakdown,
    }


@router.post("/admin/tokens/ledger/emit")
async def emit_ledger_event(payload: Dict[str, Any], _: bool = Depends(require_admin)) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "").strip()
    tokens = int(payload.get("tokens") or 0)
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if tokens == 0:
        raise HTTPException(status_code=400, detail="tokens must be non-zero")

    event = {
        "event_id": payload.get("event_id") or uuid.uuid4().hex,
        "user_id": user_id,
        "feature": payload.get("feature") or "manual_adjustment",
        "tokens": tokens,
        "kind": payload.get("kind") or ("debit" if tokens > 0 else "credit"),
        "timestamp": _iso(_utcnow()),
        "meta": payload.get("meta") or {},
    }

    store = _load_store()
    ledger = store.get("ledger")
    if not isinstance(ledger, list):
        ledger = []
    ledger.append(event)
    store["ledger"] = ledger
    _save_store(store)
    return {"event": event}
