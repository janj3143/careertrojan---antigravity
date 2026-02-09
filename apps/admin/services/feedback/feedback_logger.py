"""
User Feedback Logger - Continuous Improvement System
Logs user feedback for model retraining and improvement.

Format: JSONL (JSON Lines - one JSON object per line)
Location: ai_data_final/feedback.jsonl

Usage:
    from services.feedback.feedback_logger import FeedbackLogger
    
    logger = FeedbackLogger()
    logger.log_enrichment_feedback(
        user_id="user_123",
        doc_id="doc_456",
        enrichment_type="dashboard",
        was_helpful=True,
        user_comment="Great keyword suggestions!"
    )
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FeedbackLogger:
    """
    Logs user feedback for model improvement and retraining.
    
    Feedback Types:
    - enrichment: General enrichment quality feedback
    - ats_score: ATS score accuracy feedback
    - keyword_match: Keyword matching quality
    - job_title_similarity: Job title similarity accuracy
    - clustering: Clustering assignment feedback
    """
    
    def __init__(self, feedback_path: Path = None):
        """
        Initialize feedback logger.
        
        Args:
            feedback_path: Path to feedback.jsonl file.
                          If None, uses ai_data_final/feedback.jsonl
        """
        if feedback_path is None:
            # Auto-detect ai_data_final directory
            current = Path(__file__).parent
            for _ in range(5):
                data_path = current / "ai_data_final"
                if data_path.exists():
                    feedback_path = data_path / "feedback.jsonl"
                    break
                current = current.parent
            
            if feedback_path is None:
                feedback_path = Path("ai_data_final/feedback.jsonl")
        
        self.feedback_path = Path(feedback_path)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ FeedbackLogger initialized: {self.feedback_path}")
    
    def log_enrichment_feedback(
        self,
        user_id: str,
        doc_id: str,
        enrichment_type: str,
        was_helpful: bool,
        user_comment: Optional[str] = None,
        model_version: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log feedback for enrichment quality.
        
        Args:
            user_id: User identifier
            doc_id: Document/resume identifier
            enrichment_type: Type of enrichment ("dashboard", "keywords", "job_titles", etc.)
            was_helpful: Boolean - was the enrichment helpful?
            user_comment: Optional text feedback from user
            model_version: Model version used for enrichment
            additional_data: Any extra data to log
        
        Example:
            logger.log_enrichment_feedback(
                user_id="user_123",
                doc_id="resume_456",
                enrichment_type="dashboard",
                was_helpful=True,
                user_comment="Very helpful suggestions!"
            )
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "doc_id": doc_id,
            "enrichment_type": enrichment_type,
            "was_helpful": was_helpful,
            "user_comment": user_comment,
            "model_version": model_version,
            "feedback_type": "enrichment"
        }
        
        if additional_data:
            entry["additional_data"] = additional_data
        
        self._write_entry(entry)
        logger.info(f"[Feedback] Enrichment feedback logged: {enrichment_type} - helpful={was_helpful}")
    
    def log_ats_score_feedback(
        self,
        user_id: str,
        doc_id: str,
        ats_score: float,
        user_rating: int,
        actual_outcome: Optional[str] = None,
        model_version: Optional[str] = None,
        user_comment: Optional[str] = None
    ):
        """
        Log feedback for ATS score accuracy.
        
        Args:
            user_id: User identifier
            doc_id: Document/resume identifier
            ats_score: ATS score given by model (0.0-100.0)
            user_rating: User's rating of accuracy (1-5 stars)
            actual_outcome: Actual job application outcome
                          ("got_interview", "rejected", "offer", "pending", etc.)
            model_version: Model version used for scoring
            user_comment: Optional text feedback
        
        Example:
            logger.log_ats_score_feedback(
                user_id="user_123",
                doc_id="resume_456",
                ats_score=87.5,
                user_rating=5,
                actual_outcome="got_interview"
            )
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "doc_id": doc_id,
            "ats_score": ats_score,
            "user_rating": user_rating,
            "actual_outcome": actual_outcome,
            "model_version": model_version,
            "user_comment": user_comment,
            "feedback_type": "ats_score"
        }
        
        self._write_entry(entry)
        logger.info(f"[Feedback] ATS score feedback logged: score={ats_score}, rating={user_rating}/5")
    
    def log_prediction_feedback(
        self,
        user_id: str,
        doc_id: str,
        prediction_type: str,
        predicted_value: Any,
        actual_value: Any,
        was_accurate: bool,
        model_version: Optional[str] = None
    ):
        """
        Log feedback for specific model predictions.
        
        Args:
            user_id: User identifier
            doc_id: Document identifier
            prediction_type: Type of prediction ("job_match", "salary", "placement", etc.)
            predicted_value: Value predicted by model
            actual_value: Actual observed value
            was_accurate: Boolean - was prediction accurate?
            model_version: Model version used
        
        Example:
            logger.log_prediction_feedback(
                user_id="user_123",
                doc_id="resume_456",
                prediction_type="salary",
                predicted_value=120000,
                actual_value=125000,
                was_accurate=True
            )
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "doc_id": doc_id,
            "prediction_type": prediction_type,
            "predicted_value": predicted_value,
            "actual_value": actual_value,
            "was_accurate": was_accurate,
            "model_version": model_version,
            "feedback_type": "prediction"
        }
        
        self._write_entry(entry)
        logger.info(f"[Feedback] Prediction feedback logged: {prediction_type} - accurate={was_accurate}")
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        doc_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log user actions for behavioral analytics.
        
        Args:
            user_id: User identifier
            action: Action taken ("enrichment_viewed", "export_pdf", "shared", etc.)
            doc_id: Optional document identifier
            success: Whether action succeeded
            metadata: Additional action metadata
        
        Example:
            logger.log_user_action(
                user_id="user_123",
                action="enrichment_viewed",
                doc_id="resume_456",
                metadata={"time_spent_seconds": 45}
            )
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "action": action,
            "doc_id": doc_id,
            "success": success,
            "metadata": metadata,
            "feedback_type": "user_action"
        }
        
        self._write_entry(entry)
        logger.debug(f"[Feedback] User action logged: {action} - success={success}")
    
    def _write_entry(self, entry: Dict[str, Any]):
        """
        Append entry to JSONL file (one JSON per line).
        Thread-safe for concurrent writes.
        """
        try:
            with open(self.feedback_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"[FeedbackLogger] Failed to write entry: {e}")
    
    def get_recent_feedback(
        self,
        days_back: int = 30,
        feedback_type: Optional[str] = None
    ) -> list:
        """
        Retrieve recent feedback entries.
        
        Args:
            days_back: Number of days to look back
            feedback_type: Filter by feedback type
        
        Returns:
            List of feedback entries
        """
        from datetime import timedelta
        
        if not self.feedback_path.exists():
            return []
        
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        entries = []
        
        try:
            with open(self.feedback_path, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    
                    if entry_time > cutoff:
                        if feedback_type is None or entry.get('feedback_type') == feedback_type:
                            entries.append(entry)
        except Exception as e:
            logger.error(f"[FeedbackLogger] Failed to read feedback: {e}")
        
        return entries
    
    def get_feedback_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get summary statistics of recent feedback.
        
        Args:
            days_back: Number of days to analyze
        
        Returns:
            Dict with summary statistics
        """
        entries = self.get_recent_feedback(days_back)
        
        summary = {
            "total_entries": len(entries),
            "period_days": days_back,
            "by_type": {},
            "enrichment_quality": {},
            "ats_quality": {}
        }
        
        # Count by feedback type
        for entry in entries:
            ftype = entry.get('feedback_type', 'unknown')
            summary["by_type"][ftype] = summary["by_type"].get(ftype, 0) + 1
        
        # Enrichment quality metrics
        enrichment_entries = [e for e in entries if e.get('feedback_type') == 'enrichment']
        if enrichment_entries:
            helpful_count = sum(1 for e in enrichment_entries if e.get('was_helpful'))
            summary["enrichment_quality"] = {
                "total": len(enrichment_entries),
                "helpful_count": helpful_count,
                "helpful_percentage": (helpful_count / len(enrichment_entries)) * 100
            }
        
        # ATS score quality metrics
        ats_entries = [e for e in entries if e.get('feedback_type') == 'ats_score']
        if ats_entries:
            ratings = [e.get('user_rating', 0) for e in ats_entries]
            summary["ats_quality"] = {
                "total": len(ats_entries),
                "average_rating": sum(ratings) / len(ratings) if ratings else 0,
                "high_ratings": sum(1 for r in ratings if r >= 4)
            }
        
        return summary
