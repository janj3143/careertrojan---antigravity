"""
SQLite Database Manager for IntelliCV AI Learning System
Backend-only database operations.

Policy: no file-based fallback persistence and no fabricated/sample records.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Try multiple SQLite approaches
SQLITE_AVAILABLE = False
sqlite_conn = None

# Primary approach - built-in sqlite3
try:
    import sqlite3
    SQLITE_AVAILABLE = True
    sqlite_module = sqlite3
    print("[OK] Using built-in sqlite3")
except ImportError:
    print("[ERROR] Built-in sqlite3 not available")

# Fallback 1 - Alternative sqlite implementations
if not SQLITE_AVAILABLE:
    try:
        import apsw as sqlite3
        SQLITE_AVAILABLE = True
        sqlite_module = sqlite3
        print("[OK] Using APSW SQLite")
    except ImportError:
        pass

# Fallback 2 - File-based storage as last resort
if not SQLITE_AVAILABLE:
    print("[ERROR] SQLite not available")

class IntelliCVSQLiteManager:
    """
    Comprehensive SQLite manager for AI learning system
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite manager with database path"""
        self.db_path = db_path or "ai_data_system/ai_learning/intellicv_ai_learning.db"
        self.db_directory = Path(self.db_path).parent
        self.db_directory.mkdir(parents=True, exist_ok=True)

        self.connection = None
        self.sqlite_available = SQLITE_AVAILABLE

        if not self.sqlite_available:
            raise RuntimeError("SQLite is required; file-based fallback storage is disabled")

        self._initialize_database()

    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            self.connection = sqlite_module.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )

            # Enable WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")

            self._create_tables()
            print(f"✅ SQLite database initialized: {self.db_path}")

        except Exception as e:
            print(f"❌ SQLite initialization failed: {e}")
            raise RuntimeError(f"SQLite initialization failed: {e}")

    def _create_tables(self):
        """Create all required database tables"""

        # AI Learning Results Table
        create_ai_learning = """
        CREATE TABLE IF NOT EXISTS ai_learning_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT NOT NULL,
            processing_mode TEXT NOT NULL,
            input_type TEXT NOT NULL,
            bayesian_confidence REAL,
            nlp_sentiment REAL,
            fuzzy_logic_score REAL,
            llm_coherence REAL,
            combined_score REAL,
            processing_time REAL,
            data_size INTEGER,
            model_version TEXT,
            feedback_rating INTEGER,
            user_corrections TEXT,
            raw_input_hash TEXT,
            processed_output_hash TEXT,
            error_messages TEXT,
            metadata TEXT
        )
        """

        # Processing History Table
        create_processing_history = """
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            operation_type TEXT NOT NULL,
            input_files INTEGER DEFAULT 0,
            processed_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            total_processing_time REAL,
            average_confidence REAL,
            status TEXT NOT NULL,
            configuration TEXT,
            results_summary TEXT
        )
        """

        # Model Performance Tracking
        create_model_performance = """
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_type TEXT NOT NULL,
            accuracy_score REAL,
            precision_score REAL,
            recall_score REAL,
            f1_score REAL,
            processing_speed REAL,
            memory_usage REAL,
            training_data_size INTEGER,
            test_data_size INTEGER,
            hyperparameters TEXT,
            performance_notes TEXT
        )
        """

        # System Metrics Table
        create_system_metrics = """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu_usage REAL,
            memory_usage REAL,
            disk_usage REAL,
            active_sessions INTEGER,
            queue_length INTEGER,
            response_time REAL,
            error_rate REAL,
            throughput REAL,
            system_health TEXT
        )
        """

        tables = [
            create_ai_learning,
            create_processing_history,
            create_model_performance,
            create_system_metrics
        ]

        for table_sql in tables:
            self.connection.execute(table_sql)

        self.connection.commit()
        print("[OK] Database tables created successfully")

    def save_ai_learning_result(self, result_data: Dict[str, Any]) -> bool:
        """Save AI learning result to database."""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._save_to_sqlite('ai_learning_results', result_data)

    def save_processing_history(self, history_data: Dict[str, Any]) -> bool:
        """Save processing history"""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._save_to_sqlite('processing_history', history_data)

    def save_model_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Save model performance metrics"""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._save_to_sqlite('model_performance', performance_data)

    def save_system_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Save system metrics"""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._save_to_sqlite('system_metrics', metrics_data)

    def _save_to_sqlite(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Save data to SQLite table"""
        try:
            # Prepare column names and placeholders
            columns = list(data.keys())
            placeholders = ['?' for _ in columns]
            values = list(data.values())

            sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            """

            self.connection.execute(sql, values)
            self.connection.commit()
            return True

        except Exception as e:
            print(f"❌ SQLite save error: {e}")
            return False

    def _save_to_fallback(self, storage_key: str, data: Dict[str, Any]) -> bool:
        raise RuntimeError("File-based fallback storage is disabled")

    def get_ai_learning_stats(self) -> Dict[str, Any]:
        """Get AI learning statistics"""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._get_sqlite_stats()

    def _get_sqlite_stats(self) -> Dict[str, Any]:
        """Get statistics from SQLite database"""
        try:
            cursor = self.connection.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM ai_learning_results")
            total_records = cursor.fetchone()[0]

            # Average scores
            cursor.execute("""
                SELECT
                    AVG(bayesian_confidence),
                    AVG(nlp_sentiment),
                    AVG(fuzzy_logic_score),
                    AVG(llm_coherence),
                    AVG(combined_score)
                FROM ai_learning_results
                WHERE bayesian_confidence IS NOT NULL
            """)

            avg_scores = cursor.fetchone()

            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM ai_learning_results
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            recent_activity = cursor.fetchone()[0]

            return {
                'total_records': total_records,
                'average_bayesian_confidence': avg_scores[0] or 0,
                'average_nlp_sentiment': avg_scores[1] or 0,
                'average_fuzzy_logic_score': avg_scores[2] or 0,
                'average_llm_coherence': avg_scores[3] or 0,
                'average_combined_score': avg_scores[4] or 0,
                'recent_activity_24h': recent_activity,
                'database_type': 'SQLite'
            }

        except Exception as e:
            print(f"❌ SQLite stats error: {e}")
            return {'error': str(e), 'database_type': 'SQLite (Error)'}

    def _get_fallback_stats(self) -> Dict[str, Any]:
        raise RuntimeError("File-based fallback storage is disabled")

    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent AI learning results"""

        if not (self.sqlite_available and self.connection):
            raise RuntimeError("SQLite manager not initialized")
        return self._get_sqlite_recent_results(limit)

    def _get_sqlite_recent_results(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent results from SQLite"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM ai_learning_results
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            columns = [description[0] for description in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            print(f"❌ SQLite recent results error: {e}")
            return []

    def _get_fallback_recent_results(self, limit: int) -> List[Dict[str, Any]]:
        raise RuntimeError("File-based fallback storage is disabled")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("[OK] Database connection closed")

# Global instance for easy access
_sqlite_manager = None

def get_sqlite_manager() -> IntelliCVSQLiteManager:
    """Get global SQLite manager instance"""
    global _sqlite_manager
    if _sqlite_manager is None:
        _sqlite_manager = IntelliCVSQLiteManager()
    return _sqlite_manager

if __name__ == "__main__":
    raise RuntimeError("This module is not executable; import and use via the Admin Portal.")
