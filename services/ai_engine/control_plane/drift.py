"""
CareerTrojan — Drift Detection
===============================

Monitors AI system for performance degradation and distribution shifts.

Types of Drift:
    - Performance drift: Outcome rates declining over time
    - Prediction drift: Model confidence/output distribution changing
    - Data drift: Input characteristics changing (skill names, industries)
    - Latency drift: Response times increasing

Alerts:
    - Warning: Metrics deviating >5% from baseline
    - Critical: Metrics deviating >15% from baseline or sustained degradation

Usage:
    from services.ai_engine.control_plane import get_drift_detector
    
    detector = get_drift_detector()
    
    # Record a prediction
    detector.record_prediction(task_type="score", confidence=0.85, latency_ms=120)
    
    # Check for drift
    alerts = detector.check_drift()
    
    # Get drift report
    report = detector.get_drift_report()

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Deque

import numpy as np

logger = logging.getLogger("DriftDetector")


@dataclass
class DriftAlert:
    """A drift detection alert."""
    alert_id: str
    severity: str  # "warning", "critical"
    drift_type: str  # "performance", "prediction", "data", "latency"
    metric: str
    current_value: float
    baseline_value: float
    deviation_pct: float
    task_type: Optional[str] = None
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "drift_type": self.drift_type,
            "metric": self.metric,
            "current_value": round(self.current_value, 4),
            "baseline_value": round(self.baseline_value, 4),
            "deviation_pct": round(self.deviation_pct, 2),
            "task_type": self.task_type,
            "message": self.message,
            "timestamp": self.timestamp,
        }


@dataclass
class DriftReport:
    """Comprehensive drift analysis report."""
    summary: str
    alerts: List[DriftAlert]
    metrics: Dict[str, Dict[str, float]]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "alerts": [a.to_dict() for a in self.alerts],
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class DriftDetector:
    """
    Monitors AI system health and detects drift.
    
    Uses rolling windows to compare recent metrics against baselines.
    """
    
    # Thresholds
    WARNING_THRESHOLD = 0.05  # 5% deviation
    CRITICAL_THRESHOLD = 0.15  # 15% deviation
    
    # Rolling window sizes
    RECENT_WINDOW_HOURS = 24
    BASELINE_WINDOW_DAYS = 30
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(__file__).parent.parent / "drift_monitoring.db"
        self._lock = Lock()
        
        # In-memory rolling buffers for quick stats
        self._prediction_buffer: Dict[str, Deque] = {}
        self._buffer_max_size = 1000
        
        # Alert history
        self._recent_alerts: Deque[DriftAlert] = deque(maxlen=100)
        
        self._init_db()
        logger.info("DriftDetector initialized (db=%s)", self.db_path)
    
    def _init_db(self):
        """Initialize SQLite database for drift metrics."""
        with sqlite3.connect(self.db_path) as conn:
            # Prediction metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    confidence REAL,
                    latency_ms REAL,
                    engines_used TEXT,
                    timestamp TEXT NOT NULL,
                    hour TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pm_task ON prediction_metrics(task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pm_hour ON prediction_metrics(hour)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pm_timestamp ON prediction_metrics(timestamp)")
            
            # Aggregated hourly stats
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hour TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    count INTEGER,
                    avg_confidence REAL,
                    avg_latency_ms REAL,
                    p95_latency_ms REAL,
                    engine_distribution TEXT,
                    UNIQUE(hour, task_type)
                )
            """)
            
            # Alert history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drift_alerts (
                    alert_id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    drift_type TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    current_value REAL,
                    baseline_value REAL,
                    deviation_pct REAL,
                    task_type TEXT,
                    message TEXT,
                    timestamp TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def record_prediction(
        self,
        task_type: str,
        confidence: float,
        latency_ms: float,
        engines_used: Optional[List[str]] = None,
    ):
        """
        Record a prediction for drift monitoring.
        
        Called by the Gateway after each prediction.
        """
        now = datetime.now()
        hour = now.strftime("%Y-%m-%d-%H")
        
        # Update in-memory buffer
        with self._lock:
            if task_type not in self._prediction_buffer:
                self._prediction_buffer[task_type] = deque(maxlen=self._buffer_max_size)
            
            self._prediction_buffer[task_type].append({
                "confidence": confidence,
                "latency_ms": latency_ms,
                "engines_used": engines_used or [],
                "timestamp": now.isoformat(),
            })
        
        # Persist to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO prediction_metrics 
                    (task_type, confidence, latency_ms, engines_used, timestamp, hour)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_type,
                        confidence,
                        latency_ms,
                        json.dumps(engines_used) if engines_used else "[]",
                        now.isoformat(),
                        hour,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.debug("Failed to record prediction: %s", e)
    
    def check_drift(self) -> List[DriftAlert]:
        """
        Check for drift across all monitored dimensions.
        
        Returns list of alerts (empty if no drift detected).
        """
        alerts = []
        
        try:
            # Get recent metrics (last 24 hours)
            recent_cutoff = (datetime.now() - timedelta(hours=self.RECENT_WINDOW_HOURS)).isoformat()
            baseline_cutoff = (datetime.now() - timedelta(days=self.BASELINE_WINDOW_DAYS)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Get task types
                cursor = conn.execute("SELECT DISTINCT task_type FROM prediction_metrics")
                task_types = [row[0] for row in cursor.fetchall()]
                
                for task_type in task_types:
                    # Recent stats
                    cursor = conn.execute(
                        """
                        SELECT 
                            COUNT(*),
                            AVG(confidence),
                            AVG(latency_ms),
                            MAX(latency_ms)
                        FROM prediction_metrics
                        WHERE task_type = ? AND timestamp >= ?
                        """,
                        (task_type, recent_cutoff),
                    )
                    recent = cursor.fetchone()
                    recent_count = recent[0] or 0
                    recent_conf = recent[1] or 0
                    recent_latency = recent[2] or 0
                    recent_max_latency = recent[3] or 0
                    
                    if recent_count < 10:
                        continue  # Not enough recent data
                    
                    # Baseline stats
                    cursor = conn.execute(
                        """
                        SELECT 
                            COUNT(*),
                            AVG(confidence),
                            AVG(latency_ms),
                            MAX(latency_ms)
                        FROM prediction_metrics
                        WHERE task_type = ? AND timestamp >= ? AND timestamp < ?
                        """,
                        (task_type, baseline_cutoff, recent_cutoff),
                    )
                    baseline = cursor.fetchone()
                    baseline_count = baseline[0] or 0
                    baseline_conf = baseline[1] or 0
                    baseline_latency = baseline[2] or 0
                    
                    if baseline_count < 50:
                        continue  # Not enough baseline data
                    
                    # Check confidence drift
                    if baseline_conf > 0:
                        conf_deviation = (recent_conf - baseline_conf) / baseline_conf
                        if abs(conf_deviation) > self.WARNING_THRESHOLD:
                            alert = self._create_alert(
                                drift_type="prediction",
                                metric="confidence",
                                current=recent_conf,
                                baseline=baseline_conf,
                                deviation=conf_deviation,
                                task_type=task_type,
                            )
                            alerts.append(alert)
                    
                    # Check latency drift
                    if baseline_latency > 0:
                        latency_deviation = (recent_latency - baseline_latency) / baseline_latency
                        if latency_deviation > self.WARNING_THRESHOLD:  # Only alert on increases
                            alert = self._create_alert(
                                drift_type="latency",
                                metric="avg_latency_ms",
                                current=recent_latency,
                                baseline=baseline_latency,
                                deviation=latency_deviation,
                                task_type=task_type,
                            )
                            alerts.append(alert)
                    
                    # Check for latency spikes
                    if recent_max_latency > baseline_latency * 5:
                        alert = self._create_alert(
                            drift_type="latency",
                            metric="max_latency_spike",
                            current=recent_max_latency,
                            baseline=baseline_latency,
                            deviation=(recent_max_latency - baseline_latency) / baseline_latency,
                            task_type=task_type,
                        )
                        alerts.append(alert)
            
            # Check performance drift from outcome tracker
            try:
                from services.ai_engine.control_plane.ground_truth import get_outcome_tracker
                tracker = get_outcome_tracker()
                outcome_metrics = tracker.get_drift_metrics(days=7, comparison_days=30)
                
                for outcome_type, metrics in outcome_metrics.items():
                    if isinstance(metrics, dict) and metrics.get("significant"):
                        drift = metrics.get("drift", 0)
                        alert = self._create_alert(
                            drift_type="performance",
                            metric=f"outcome_{outcome_type}",
                            current=metrics.get("recent_rate", 0),
                            baseline=metrics.get("baseline_rate", 0),
                            deviation=drift / metrics.get("baseline_rate", 1) if metrics.get("baseline_rate", 0) > 0 else 0,
                        )
                        alerts.append(alert)
            except Exception:
                pass  # Outcome tracker may not be available
            
            # Store alerts
            for alert in alerts:
                self._store_alert(alert)
                self._recent_alerts.append(alert)
            
        except Exception as e:
            logger.exception("Drift check failed: %s", e)
        
        return alerts
    
    def _create_alert(
        self,
        drift_type: str,
        metric: str,
        current: float,
        baseline: float,
        deviation: float,
        task_type: Optional[str] = None,
    ) -> DriftAlert:
        """Create a drift alert."""
        import uuid
        
        severity = "critical" if abs(deviation) > self.CRITICAL_THRESHOLD else "warning"
        
        direction = "increased" if deviation > 0 else "decreased"
        message = f"{metric} has {direction} by {abs(deviation)*100:.1f}% for {task_type or 'all tasks'}"
        
        if drift_type == "latency" and deviation > 0:
            message += " - may indicate performance degradation"
        elif drift_type == "performance" and deviation < 0:
            message += " - outcome rates declining"
        
        return DriftAlert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            drift_type=drift_type,
            metric=metric,
            current_value=current,
            baseline_value=baseline,
            deviation_pct=deviation * 100,
            task_type=task_type,
            message=message,
        )
    
    def _store_alert(self, alert: DriftAlert):
        """Store alert in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO drift_alerts
                    (alert_id, severity, drift_type, metric, current_value, baseline_value, 
                     deviation_pct, task_type, message, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.alert_id,
                        alert.severity,
                        alert.drift_type,
                        alert.metric,
                        alert.current_value,
                        alert.baseline_value,
                        alert.deviation_pct,
                        alert.task_type,
                        alert.message,
                        alert.timestamp,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.debug("Failed to store alert: %s", e)
    
    def get_drift_report(self) -> DriftReport:
        """Generate comprehensive drift report."""
        alerts = self.check_drift()
        
        # Collect metrics
        metrics = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Per task-type metrics
                cursor = conn.execute("""
                    SELECT task_type, 
                           COUNT(*),
                           AVG(confidence),
                           AVG(latency_ms)
                    FROM prediction_metrics
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY task_type
                """)
                
                for row in cursor.fetchall():
                    task = row[0]
                    metrics[task] = {
                        "count_24h": row[1],
                        "avg_confidence": round(row[2] or 0, 4),
                        "avg_latency_ms": round(row[3] or 0, 2),
                    }
        except Exception as e:
            logger.debug("Failed to collect metrics: %s", e)
        
        # Generate recommendations
        recommendations = []
        
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        warning_count = sum(1 for a in alerts if a.severity == "warning")
        
        if critical_count > 0:
            recommendations.append("🔴 Immediate investigation required for critical alerts")
        
        latency_alerts = [a for a in alerts if a.drift_type == "latency"]
        if latency_alerts:
            recommendations.append("Consider scaling infrastructure or optimizing slow engines")
        
        performance_alerts = [a for a in alerts if a.drift_type == "performance"]
        if performance_alerts:
            recommendations.append("Review recent model changes and run regression tests")
            recommendations.append("Consider retraining models with fresh data")
        
        prediction_alerts = [a for a in alerts if a.drift_type == "prediction"]
        if prediction_alerts:
            recommendations.append("Check for data distribution changes in inputs")
            recommendations.append("Re-calibrate confidence models")
        
        if not alerts:
            recommendations.append("✅ No drift detected - system operating normally")
        
        # Summary
        if critical_count > 0:
            summary = f"🔴 CRITICAL: {critical_count} critical alert(s) require immediate attention"
        elif warning_count > 0:
            summary = f"🟡 WARNING: {warning_count} warning(s) detected - monitoring recommended"
        else:
            summary = "🟢 HEALTHY: No significant drift detected"
        
        return DriftReport(
            summary=summary,
            alerts=alerts,
            metrics=metrics,
            recommendations=recommendations,
        )
    
    def get_recent_alerts(self, limit: int = 50) -> List[DriftAlert]:
        """Get recent alerts from database."""
        alerts = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM drift_alerts 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (limit,),
                )
                for row in cursor.fetchall():
                    alerts.append(DriftAlert(
                        alert_id=row[0],
                        severity=row[1],
                        drift_type=row[2],
                        metric=row[3],
                        current_value=row[4],
                        baseline_value=row[5],
                        deviation_pct=row[6],
                        task_type=row[7],
                        message=row[8],
                        timestamp=row[9],
                    ))
        except Exception as e:
            logger.debug("Failed to get recent alerts: %s", e)
        return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE drift_alerts SET acknowledged = 1 WHERE alert_id = ?",
                    (alert_id,),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.debug("Failed to acknowledge alert: %s", e)
            return False
    
    def get_historical_trends(
        self,
        task_type: str,
        metric: str = "confidence",
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get historical trend data for visualization."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        data = {"dates": [], "values": []}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if metric == "confidence":
                    cursor = conn.execute(
                        """
                        SELECT DATE(timestamp), AVG(confidence)
                        FROM prediction_metrics
                        WHERE task_type = ? AND timestamp >= ?
                        GROUP BY DATE(timestamp)
                        ORDER BY DATE(timestamp)
                        """,
                        (task_type, cutoff),
                    )
                elif metric == "latency":
                    cursor = conn.execute(
                        """
                        SELECT DATE(timestamp), AVG(latency_ms)
                        FROM prediction_metrics
                        WHERE task_type = ? AND timestamp >= ?
                        GROUP BY DATE(timestamp)
                        ORDER BY DATE(timestamp)
                        """,
                        (task_type, cutoff),
                    )
                elif metric == "volume":
                    cursor = conn.execute(
                        """
                        SELECT DATE(timestamp), COUNT(*)
                        FROM prediction_metrics
                        WHERE task_type = ? AND timestamp >= ?
                        GROUP BY DATE(timestamp)
                        ORDER BY DATE(timestamp)
                        """,
                        (task_type, cutoff),
                    )
                else:
                    return data
                
                for row in cursor.fetchall():
                    data["dates"].append(row[0])
                    data["values"].append(round(row[1], 4) if row[1] else 0)
                    
        except Exception as e:
            logger.debug("Failed to get historical trends: %s", e)
        
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM prediction_metrics")
                total_predictions = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM drift_alerts WHERE acknowledged = 0")
                unacked_alerts = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT task_type, COUNT(*) FROM prediction_metrics GROUP BY task_type"
                )
                by_task = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    "total_predictions_tracked": total_predictions,
                    "unacknowledged_alerts": unacked_alerts,
                    "predictions_by_task": by_task,
                    "in_memory_buffer_sizes": {k: len(v) for k, v in self._prediction_buffer.items()},
                }
        except Exception as e:
            return {"error": str(e)}


# ── Module-level Singleton ───────────────────────────────────────────────

_detector_instance: Optional[DriftDetector] = None
_detector_lock = Lock()


def get_drift_detector() -> DriftDetector:
    """Get the module-level DriftDetector singleton."""
    global _detector_instance
    
    with _detector_lock:
        if _detector_instance is None:
            _detector_instance = DriftDetector()
        return _detector_instance
