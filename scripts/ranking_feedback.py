#!/usr/bin/env python3
"""
ranking_feedback.py — Match accept/reject → ranking model update
=================================================================

Purpose:
  Ingests user feedback events (accept / reject / skip for candidate–job
  matches) and incrementally updates the ranking model so future match
  scores reflect real-world preferences.

Workflow:
  1. Load feedback events from JSON file or the database
  2. Convert to pairwise training samples (accepted > rejected)
  3. Fine-tune the ranking model (gradient-boosted or neural re-ranker)
  4. Evaluate on held-out set, log metrics
  5. Save updated model artefact to trained_models/

Usage:
  python scripts/ranking_feedback.py --feedback data/feedback/events.json
  python scripts/ranking_feedback.py --feedback data/feedback/events.json --epochs 5 --lr 0.001
  python scripts/ranking_feedback.py --from-db  (reads from PostgreSQL feedback table)
"""

import argparse
import json
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.ai_engine.config import models_path, log_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ranking_feedback")


# ── Feedback data structures ─────────────────────────────────────

class FeedbackEvent:
    """Single user feedback event."""
    __slots__ = ("user_id", "match_id", "candidate_id", "job_id", "action", "timestamp", "features")

    def __init__(self, raw: dict):
        self.user_id = raw.get("user_id", "unknown")
        self.match_id = raw.get("match_id", "")
        self.candidate_id = raw.get("candidate_id", "")
        self.job_id = raw.get("job_id", "")
        self.action = raw.get("action", "skip")  # accept | reject | skip
        self.timestamp = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
        self.features = np.array(raw.get("features", [0.0] * 16), dtype=np.float32)


def load_feedback_file(path: Path) -> List[FeedbackEvent]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    events = data if isinstance(data, list) else data.get("events", [])
    return [FeedbackEvent(e) for e in events]


def load_feedback_db() -> List[FeedbackEvent]:
    """
    Reads feedback from PostgreSQL feedback table.
    Falls back to empty list if DB is unreachable.
    """
    try:
        import psycopg2
        from services.ai_engine.config import get_db_url

        db_url = get_db_url()
        # psycopg2 needs libpq-style URL; convert if asyncpg style
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, match_id, candidate_id, job_id, action, timestamp, features
            FROM match_feedback
            WHERE processed = false
            ORDER BY timestamp
            LIMIT 10000
        """)
        rows = cur.fetchall()
        events = []
        for r in rows:
            events.append(FeedbackEvent({
                "user_id": r[0], "match_id": r[1], "candidate_id": r[2],
                "job_id": r[3], "action": r[4], "timestamp": str(r[5]),
                "features": json.loads(r[6]) if r[6] else [0.0] * 16,
            }))
        cur.close()
        conn.close()
        logger.info(f"Loaded {len(events)} feedback events from DB")
        return events
    except Exception as exc:
        logger.warning(f"DB feedback load failed ({exc}) — returning empty list")
        return []


# ── Pairwise sample generation ───────────────────────────────────

def generate_pairwise_samples(events: List[FeedbackEvent]) -> Tuple[np.ndarray, np.ndarray]:
    """
    From feedback events, create pairwise training data:
      for each (accepted, rejected) pair with the same job_id,
      create a sample where features_accepted should score higher.

    Returns (X, y) where X = feature diffs, y = 1.0 (always positive direction).
    """
    by_job: Dict[str, Dict[str, List[FeedbackEvent]]] = {}
    for ev in events:
        if ev.action not in ("accept", "reject"):
            continue
        by_job.setdefault(ev.job_id, {"accept": [], "reject": []})
        by_job[ev.job_id][ev.action].append(ev)

    X_list, y_list = [], []
    for jid, groups in by_job.items():
        for acc in groups["accept"]:
            for rej in groups["reject"]:
                diff = acc.features - rej.features
                X_list.append(diff)
                y_list.append(1.0)

    if not X_list:
        return np.empty((0, 16), dtype=np.float32), np.empty(0, dtype=np.float32)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32)


# ── Ranking model update ─────────────────────────────────────────

def update_ranking_model(
    X: np.ndarray,
    y: np.ndarray,
    model_path: Path,
    epochs: int = 3,
    lr: float = 0.001,
) -> dict:
    """
    Incrementally updates the ranking model.
    Uses scikit-learn GradientBoostingClassifier as the base ranker.
    Falls back to training from scratch if no prior model exists.
    """
    import pickle
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score

    metrics: dict = {"samples": len(X), "epochs": epochs}

    if len(X) < 10:
        logger.warning("Too few pairwise samples (<10) — skipping update")
        metrics["status"] = "skipped"
        metrics["reason"] = "insufficient_samples"
        return metrics

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Load existing model or create new
    if model_path.exists():
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        logger.info("Loaded existing ranking model for incremental update")
        # Warm-start: set n_estimators += epochs * 10
        model.set_params(n_estimators=model.n_estimators + epochs * 10, warm_start=True)
    else:
        model = GradientBoostingClassifier(
            n_estimators=epochs * 50,
            learning_rate=lr,
            max_depth=4,
            warm_start=True,
            random_state=42,
        )

    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs) if len(set(y_test)) > 1 else acc

    metrics.update({"accuracy": round(acc, 4), "auc": round(auc, 4), "status": "success"})
    logger.info(f"Ranking model — acc={acc:.4f}  auc={auc:.4f}")

    # Save
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Saved ranking model → {model_path}")

    return metrics


# ── Run log ──────────────────────────────────────────────────────

def write_run_log(metrics: dict):
    log_dir = log_root / "ranking_feedback"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = log_dir / f"feedback_update_{stamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Run log → {path}")


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Match feedback → ranking model update")
    parser.add_argument("--feedback", type=str, default=None, help="Path to feedback JSON file")
    parser.add_argument("--from-db", action="store_true", help="Read feedback from PostgreSQL")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs / boosting rounds multiplier")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--model-path", type=str, default=None, help="Path to ranking model pickle")
    args = parser.parse_args()

    model_path = Path(args.model_path) if args.model_path else models_path / "ranking_model.pkl"

    t0 = time.time()

    # Load feedback
    if args.feedback:
        events = load_feedback_file(Path(args.feedback))
    elif args.from_db:
        events = load_feedback_db()
    else:
        logger.error("Provide --feedback <path> or --from-db")
        return 1

    if not events:
        logger.warning("No feedback events — nothing to do")
        return 0

    logger.info(f"Loaded {len(events)} feedback events")

    # Generate pairwise samples
    X, y = generate_pairwise_samples(events)
    logger.info(f"Generated {len(X)} pairwise training samples")

    # Update model
    metrics = update_ranking_model(X, y, model_path, epochs=args.epochs, lr=args.lr)
    metrics["feedback_count"] = len(events)
    metrics["duration_s"] = round(time.time() - t0, 2)

    write_run_log(metrics)
    print(f"{'✅' if metrics.get('status') == 'success' else '⚠️'} Ranking feedback update complete in {metrics['duration_s']}s")
    return 0 if metrics.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
