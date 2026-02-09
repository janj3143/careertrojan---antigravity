"""
AI Learning Pattern Tracker
Provides visibility into AI learning progress for admin dashboard
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json

class AILearningPatternTracker:
    """
    Track and display AI learning patterns for admin visibility
    Shows concrete evidence of AI improvement over time
    """

    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "admin_portal" / "db" / "ai_learning_history.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_database()

    def initialize_database(self):
        """Create learning history tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Unknown patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unknown_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL,
                action TEXT,
                resolution TEXT,
                exa_researched INTEGER DEFAULT 0,
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Processing accuracy history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_processed INTEGER,
                successful INTEGER,
                failed INTEGER,
                accuracy_pct REAL,
                threshold_pct REAL,
                passes_threshold INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Confidence score history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                avg_confidence REAL,
                min_confidence REAL,
                max_confidence REAL,
                sample_size INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Data consolidation events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consolidation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                duplicate_values TEXT NOT NULL,
                canonical_value TEXT NOT NULL,
                confidence REAL,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def track_unknown_pattern(self, pattern_type: str, value: str, confidence: float = 0.0):
        """
        Track when AI encounters unknown pattern

        Args:
            pattern_type: 'job_title', 'company', 'skill', 'location', etc.
            value: The unknown value encountered
            confidence: Initial confidence score (usually low for unknowns)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO unknown_patterns
            (timestamp, pattern_type, value, confidence, action, exa_researched)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            pattern_type,
            value,
            confidence,
            'flagged_for_research',
            0
        ))

        conn.commit()
        conn.close()

    def track_exa_research(self, pattern_type: str, value: str, exa_result: Dict):
        """
        Track when Exa research resolves unknown pattern

        Args:
            pattern_type: Type of pattern researched
            value: The value that was researched
            exa_result: Results from Exa API
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update the unknown pattern record
        cursor.execute("""
            UPDATE unknown_patterns
            SET exa_researched = 1,
                resolution = ?,
                resolved_at = ?,
                confidence = ?
            WHERE pattern_type = ? AND value = ? AND exa_researched = 0
        """, (
            json.dumps(exa_result),
            datetime.now().isoformat(),
            0.85,  # High confidence after Exa research
            pattern_type,
            value
        ))

        conn.commit()
        conn.close()

    def track_processing_accuracy(self, total: int, successful: int, failed: int, threshold: float = 70.0):
        """
        Track real processing accuracy (NOT hardcoded)

        Args:
            total: Total files processed
            successful: Successfully processed files
            failed: Failed processing files
            threshold: Minimum acceptable accuracy
        """
        accuracy = (successful / total * 100) if total > 0 else 0.0
        passes = 1 if accuracy >= threshold else 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO processing_accuracy
            (timestamp, total_processed, successful, failed, accuracy_pct, threshold_pct, passes_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            total,
            successful,
            failed,
            accuracy,
            threshold,
            passes
        ))

        conn.commit()
        conn.close()

    def track_confidence_scores(self, category: str, scores: List[float]):
        """
        Track confidence score distribution over time

        Args:
            category: Data category (candidates, companies, job_titles, etc.)
            scores: List of confidence scores from recent processing
        """
        if not scores:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO confidence_history
            (timestamp, category, avg_confidence, min_confidence, max_confidence, sample_size)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            category,
            sum(scores) / len(scores),
            min(scores),
            max(scores),
            len(scores)
        ))

        conn.commit()
        conn.close()

    def track_consolidation(self, entity_type: str, duplicates: List[str], canonical: str, source: str = 'ai_learning'):
        """
        Track when AI consolidates duplicate entities

        Args:
            entity_type: 'company', 'job_title', 'location', etc.
            duplicates: List of duplicate values found
            canonical: The canonical/standard value chosen
            source: How consolidation was determined
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO consolidation_events
            (timestamp, entity_type, duplicate_values, canonical_value, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            entity_type,
            json.dumps(duplicates),
            canonical,
            0.80,
            source
        ))

        conn.commit()
        conn.close()

    def get_learning_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate learning improvement metrics over time period

        Returns:
            Dictionary with learning metrics proving AI is improving
        """
        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Unknown patterns trend (should decrease)
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as count
            FROM unknown_patterns
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (since_date,))

        unknown_trend = cursor.fetchall()

        # 2. Exa research efficiency (research calls should decrease)
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                SUM(exa_researched) as researched,
                COUNT(*) as total
            FROM unknown_patterns
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (since_date,))

        research_trend = cursor.fetchall()

        # 3. Processing accuracy trend (should increase or stabilize)
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                AVG(accuracy_pct) as avg_accuracy,
                AVG(passes_threshold) as pass_rate
            FROM processing_accuracy
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (since_date,))

        accuracy_trend = cursor.fetchall()

        # 4. Confidence improvement (should increase)
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                category,
                AVG(avg_confidence) as avg_conf
            FROM confidence_history
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp), category
            ORDER BY date, category
        """, (since_date,))

        confidence_trend = cursor.fetchall()

        # 5. Consolidation activity (proves learning)
        cursor.execute("""
            SELECT
                entity_type,
                COUNT(*) as consolidations
            FROM consolidation_events
            WHERE timestamp >= ?
            GROUP BY entity_type
        """, (since_date,))

        consolidations = cursor.fetchall()

        conn.close()

        return {
            'unknown_patterns_trend': unknown_trend,
            'research_efficiency': research_trend,
            'accuracy_trend': accuracy_trend,
            'confidence_improvement': confidence_trend,
            'consolidation_activity': consolidations,
            'period_days': days,
            'analysis_date': datetime.now().isoformat()
        }

    def get_learning_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get concise learning summary for dashboard display

        Returns admin-friendly metrics showing AI is learning
        """
        metrics = self.get_learning_metrics(days)

        # Calculate improvements
        unknown_first = metrics['unknown_patterns_trend'][0][1] if metrics['unknown_patterns_trend'] else 0
        unknown_last = metrics['unknown_patterns_trend'][-1][1] if metrics['unknown_patterns_trend'] else 0
        unknown_improvement = ((unknown_first - unknown_last) / unknown_first * 100) if unknown_first > 0 else 0

        accuracy_first = metrics['accuracy_trend'][0][1] if metrics['accuracy_trend'] else 0
        accuracy_last = metrics['accuracy_trend'][-1][1] if metrics['accuracy_trend'] else 0
        accuracy_improvement = accuracy_last - accuracy_first

        return {
            'unknown_patterns_reduced': unknown_improvement,
            'current_accuracy': accuracy_last,
            'accuracy_improvement': accuracy_improvement,
            'total_consolidations': sum(c[1] for c in metrics['consolidation_activity']),
            'learning_active': unknown_improvement > 0 or accuracy_improvement > 0,
            'period_days': days
        }

# Global instance
_tracker_instance = None

def get_learning_tracker() -> AILearningPatternTracker:
    """Get singleton instance of learning tracker"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = AILearningPatternTracker()
    return _tracker_instance
