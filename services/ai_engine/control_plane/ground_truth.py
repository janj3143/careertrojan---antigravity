"""
CareerTrojan — Ground-Truth Tracker
====================================

Records outcome signals to correlate AI predictions with real-world results.

Outcome Types:
    - interview_requested: User received an interview callback
    - offer_received: User got a job offer
    - recommendation_accepted: User followed AI recommendation
    - rewrite_adopted: User used AI-rewritten content
    - question_helpful: User rated interview question as helpful
    - match_applied: User applied to a matched job
    - ats_passed: CV passed ATS screening
    - mentor_rating: Mentor's assessment of mentee progress

This data enables:
    - Calibration of confidence scores
    - Identification of model drift
    - A/B testing of model versions
    - ROI measurement of AI features

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import sqlite3
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("OutcomeTracker")


@dataclass
class OutcomeRecord:
    """A single outcome observation."""
    record_id: str
    request_id: str
    outcome_type: str
    outcome_value: Any
    user_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "request_id": self.request_id,
            "outcome_type": self.outcome_type,
            "outcome_value": self.outcome_value,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class OutcomeTracker:
    """
    Ground-truth loop for AI model validation.
    
    Stores outcomes in SQLite for efficient querying and aggregation.
    Correlates outcomes with prediction request_ids.
    """
    
    OUTCOME_TYPES = {
        "interview_requested": {"positive": True, "weight": 1.0},
        "offer_received": {"positive": True, "weight": 2.0},
        "recommendation_accepted": {"positive": True, "weight": 0.5},
        "recommendation_rejected": {"positive": False, "weight": 0.5},
        "rewrite_adopted": {"positive": True, "weight": 0.7},
        "rewrite_discarded": {"positive": False, "weight": 0.3},
        "question_helpful": {"positive": True, "weight": 0.3},
        "question_not_helpful": {"positive": False, "weight": 0.3},
        "match_applied": {"positive": True, "weight": 0.8},
        "match_ignored": {"positive": False, "weight": 0.2},
        "ats_passed": {"positive": True, "weight": 1.0},
        "ats_failed": {"positive": False, "weight": 1.0},
        "mentor_rating": {"positive": None, "weight": 1.0},  # Numeric
        "user_feedback_score": {"positive": None, "weight": 0.5},  # 1-5
    }
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(__file__).parent.parent / "outcome_tracking.db"
        self._lock = Lock()
        
        # In-memory cache for quick stats
        self._cache: Dict[str, List[OutcomeRecord]] = {}
        self._cache_max_per_type = 1000
        
        self._init_db()
        logger.info("OutcomeTracker initialized (db=%s)", self.db_path)
    
    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    record_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    outcome_type TEXT NOT NULL,
                    outcome_value TEXT,
                    user_id TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_request_id ON outcomes(request_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcome_type ON outcomes(outcome_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON outcomes(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON outcomes(timestamp)")
            
            # Prediction-outcome correlation table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    task_type TEXT,
                    predicted_value TEXT,
                    confidence REAL,
                    calibrated_confidence REAL,
                    outcome_type TEXT,
                    outcome_value TEXT,
                    correlation_score REAL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(request_id, outcome_type)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_po_request ON prediction_outcomes(request_id)")
            
            conn.commit()
    
    def record(
        self,
        request_id: str,
        outcome_type: str,
        outcome_value: Any,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record an outcome signal.
        
        Args:
            request_id: The AI request this outcome is associated with
            outcome_type: Type of outcome (see OUTCOME_TYPES)
            outcome_value: The outcome value (boolean, numeric, or string)
            user_id: Optional user identifier
            metadata: Additional context
        
        Returns:
            True if recorded successfully
        """
        import uuid
        
        record = OutcomeRecord(
            record_id=str(uuid.uuid4()),
            request_id=request_id,
            outcome_type=outcome_type,
            outcome_value=outcome_value,
            user_id=user_id,
            metadata=metadata or {},
        )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO outcomes (record_id, request_id, outcome_type, outcome_value, user_id, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.record_id,
                        record.request_id,
                        record.outcome_type,
                        json.dumps(record.outcome_value),
                        record.user_id,
                        record.timestamp,
                        json.dumps(record.metadata),
                    ),
                )
                conn.commit()
            
            # Update in-memory cache
            with self._lock:
                if outcome_type not in self._cache:
                    self._cache[outcome_type] = []
                self._cache[outcome_type].append(record)
                if len(self._cache[outcome_type]) > self._cache_max_per_type:
                    self._cache[outcome_type] = self._cache[outcome_type][-self._cache_max_per_type // 2:]
            
            logger.debug("Recorded outcome: %s for request %s", outcome_type, request_id)
            return True
            
        except Exception as e:
            logger.exception("Failed to record outcome: %s", e)
            return False
    
    def link_prediction(
        self,
        request_id: str,
        task_type: str,
        predicted_value: Any,
        confidence: float,
        calibrated_confidence: float,
    ):
        """
        Link a prediction to enable outcome correlation.
        
        Called by the gateway after each prediction.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO prediction_outcomes 
                    (request_id, task_type, predicted_value, confidence, calibrated_confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        task_type,
                        json.dumps(predicted_value) if not isinstance(predicted_value, str) else predicted_value,
                        confidence,
                        calibrated_confidence,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.debug("Failed to link prediction: %s", e)
    
    def get_outcomes_for_request(self, request_id: str) -> List[OutcomeRecord]:
        """Get all outcomes for a specific request."""
        records = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM outcomes WHERE request_id = ?",
                    (request_id,),
                )
                for row in cursor.fetchall():
                    records.append(OutcomeRecord(
                        record_id=row[0],
                        request_id=row[1],
                        outcome_type=row[2],
                        outcome_value=json.loads(row[3]) if row[3] else None,
                        user_id=row[4],
                        timestamp=row[5],
                        metadata=json.loads(row[6]) if row[6] else {},
                    ))
        except Exception as e:
            logger.exception("Failed to get outcomes: %s", e)
        return records
    
    def get_outcome_rates(
        self,
        outcome_type: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Calculate outcome rates for a given type.
        
        Returns:
            - total_count: Number of outcomes
            - positive_rate: Fraction of positive outcomes
            - by_task_type: Breakdown by task type
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total outcomes
                cursor = conn.execute(
                    """
                    SELECT COUNT(*), 
                           SUM(CASE WHEN json_extract(outcome_value, '$') IN ('true', '1') THEN 1 ELSE 0 END)
                    FROM outcomes 
                    WHERE outcome_type = ? AND timestamp >= ?
                    """,
                    (outcome_type, cutoff),
                )
                row = cursor.fetchone()
                total = row[0] or 0
                positive = row[1] or 0
                
                # By task type
                cursor = conn.execute(
                    """
                    SELECT po.task_type, COUNT(*), 
                           SUM(CASE WHEN json_extract(o.outcome_value, '$') IN ('true', '1') THEN 1 ELSE 0 END)
                    FROM outcomes o
                    JOIN prediction_outcomes po ON o.request_id = po.request_id
                    WHERE o.outcome_type = ? AND o.timestamp >= ?
                    GROUP BY po.task_type
                    """,
                    (outcome_type, cutoff),
                )
                by_task = {}
                for row in cursor.fetchall():
                    task = row[0] or "unknown"
                    by_task[task] = {
                        "total": row[1],
                        "positive": row[2] or 0,
                        "rate": (row[2] or 0) / row[1] if row[1] > 0 else 0,
                    }
                
                return {
                    "outcome_type": outcome_type,
                    "days": days,
                    "total_count": total,
                    "positive_count": positive,
                    "positive_rate": positive / total if total > 0 else 0,
                    "by_task_type": by_task,
                }
                
        except Exception as e:
            logger.exception("Failed to calculate outcome rates")
            return {"error": str(e)}
    
    def get_calibration_data(
        self,
        task_type: str,
        outcome_type: str,
        days: int = 90,
    ) -> List[Tuple[float, bool]]:
        """
        Get (confidence, outcome) pairs for calibration.
        
        Used by ConfidenceCalibrator to train calibration models.
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        pairs = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT po.confidence, o.outcome_value
                    FROM prediction_outcomes po
                    JOIN outcomes o ON po.request_id = o.request_id
                    WHERE po.task_type = ? 
                      AND o.outcome_type = ?
                      AND o.timestamp >= ?
                    """,
                    (task_type, outcome_type, cutoff),
                )
                for row in cursor.fetchall():
                    conf = row[0]
                    val = json.loads(row[1]) if row[1] else False
                    if isinstance(val, bool):
                        pairs.append((conf, val))
                    elif isinstance(val, (int, float)):
                        pairs.append((conf, val > 0.5))
        except Exception as e:
            logger.exception("Failed to get calibration data")
        
        return pairs
    
    def get_drift_metrics(
        self,
        days: int = 7,
        comparison_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Compare recent outcome rates to historical baseline.
        
        Used by DriftDetector to identify performance degradation.
        """
        recent_cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        baseline_cutoff = (datetime.now() - timedelta(days=comparison_days)).isoformat()
        
        metrics = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for outcome_type, config in self.OUTCOME_TYPES.items():
                    if config["positive"] is None:
                        continue  # Skip numeric outcomes
                    
                    # Recent rate
                    cursor = conn.execute(
                        """
                        SELECT COUNT(*), 
                               SUM(CASE WHEN json_extract(outcome_value, '$') IN ('true', '1') THEN 1 ELSE 0 END)
                        FROM outcomes 
                        WHERE outcome_type = ? AND timestamp >= ?
                        """,
                        (outcome_type, recent_cutoff),
                    )
                    recent = cursor.fetchone()
                    recent_total = recent[0] or 0
                    recent_positive = recent[1] or 0
                    recent_rate = recent_positive / recent_total if recent_total > 0 else 0
                    
                    # Baseline rate
                    cursor = conn.execute(
                        """
                        SELECT COUNT(*), 
                               SUM(CASE WHEN json_extract(outcome_value, '$') IN ('true', '1') THEN 1 ELSE 0 END)
                        FROM outcomes 
                        WHERE outcome_type = ? AND timestamp >= ? AND timestamp < ?
                        """,
                        (outcome_type, baseline_cutoff, recent_cutoff),
                    )
                    baseline = cursor.fetchone()
                    baseline_total = baseline[0] or 0
                    baseline_positive = baseline[1] or 0
                    baseline_rate = baseline_positive / baseline_total if baseline_total > 0 else 0
                    
                    drift = recent_rate - baseline_rate
                    
                    metrics[outcome_type] = {
                        "recent_rate": round(recent_rate, 4),
                        "baseline_rate": round(baseline_rate, 4),
                        "drift": round(drift, 4),
                        "drift_pct": round(drift / baseline_rate * 100, 2) if baseline_rate > 0 else 0,
                        "recent_count": recent_total,
                        "baseline_count": baseline_total,
                        "significant": abs(drift) > 0.05 and recent_total >= 10,
                    }
        
        except Exception as e:
            logger.exception("Failed to calculate drift metrics")
            metrics["error"] = str(e)
        
        return metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM outcomes")
                total = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT outcome_type, COUNT(*) FROM outcomes GROUP BY outcome_type ORDER BY COUNT(*) DESC"
                )
                by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                cursor = conn.execute("SELECT COUNT(DISTINCT request_id) FROM prediction_outcomes")
                linked_predictions = cursor.fetchone()[0]
                
                return {
                    "total_outcomes": total,
                    "by_type": by_type,
                    "linked_predictions": linked_predictions,
                    "outcome_types_supported": list(self.OUTCOME_TYPES.keys()),
                }
        except Exception as e:
            logger.exception("Failed to get stats")
            return {"error": str(e)}


# ── Module-level Singleton ───────────────────────────────────────────────

_tracker_instance: Optional[OutcomeTracker] = None
_tracker_lock = Lock()


def get_outcome_tracker() -> OutcomeTracker:
    """Get the module-level OutcomeTracker singleton."""
    global _tracker_instance
    
    with _tracker_lock:
        if _tracker_instance is None:
            _tracker_instance = OutcomeTracker()
        return _tracker_instance
