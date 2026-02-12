"""
CareerTrojan — Collocation Data Loader
=======================================
Bridges the collocation engine's gazetteer loading with the project data layer.

Responsibilities:
  1. Load gazetteers from L: drive (source of truth) at startup
  2. Sync gazetteers to local project C: drive for Docker/production
  3. Provide hooks for user-login enrichment events
  4. Schedule periodic ingestion of user interaction logs

Usage:
    from services.ai_engine.collocation_data_loader import (
        bootstrap_collocation_engine,
        handle_user_login_event,
    )

    # At app startup
    stats = bootstrap_collocation_engine()

    # On user login (called from auth middleware)
    result = handle_user_login_event(user_data)

Author: CareerTrojan System
Date: February 2026
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def bootstrap_collocation_engine(sync_local: bool = True) -> Dict[str, Any]:
    """
    Initialize the collocation engine with all gazetteer data.
    Should be called once at application startup.

    Args:
        sync_local: whether to copy gazetteers from L: to local C: drive

    Returns:
        Engine learning stats after initialization
    """
    from services.ai_engine.collocation_engine import collocation_engine

    # Load all gazetteer JSON files from the gazetteers/ folder
    loaded = collocation_engine.load_gazetteers()

    # Optionally sync to local project directory
    if sync_local:
        try:
            sync_result = collocation_engine.sync_gazetteers_to_local()
            logger.info("Gazetteer sync: %s", sync_result)
        except Exception as e:
            logger.warning("Gazetteer sync to local failed (non-fatal): %s", e)

    stats = collocation_engine.get_learning_stats()
    logger.info(
        "Collocation engine bootstrapped: %d seed + %d learned + %d gazetteer = %d total phrases",
        stats["seed_phrase_count"],
        stats["learned_phrase_count"],
        loaded,
        stats["total_known_phrases"],
    )
    return stats


def handle_user_login_event(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a user login event for collocation learning.
    Call this from auth middleware or the login endpoint.

    Args:
        user_data: dict with keys like:
            - "skills": ["Machine Learning", "Data Analysis", ...]
            - "job_title": "Senior Process Engineer"
            - "industry": "Oil & Gas"
            - "cv_text": "Full resume text..."
            - "recent_searches": ["PLC engineer Houston", ...]
            - "bio": "Profile bio text..."

    Returns:
        Enrichment result summary
    """
    from services.ai_engine.collocation_engine import collocation_engine

    try:
        result = collocation_engine.on_user_login(user_data)
        logger.info("User login enrichment: %s", result)
        return result
    except Exception as e:
        logger.error("User login enrichment failed: %s", e)
        return {"error": str(e)}


def ingest_recent_interactions(hours: int = 24) -> Dict[str, Any]:
    """
    Bulk-ingest user interaction log files from the past N hours.
    Call this periodically (e.g. via enrichment watchdog or cron).

    Args:
        hours: look back this many hours for new interaction files

    Returns:
        Ingestion result summary
    """
    from services.ai_engine.collocation_engine import collocation_engine

    try:
        result = collocation_engine.ingest_interaction_files(since_hours=hours)
        logger.info("Interaction ingestion: %s", result)
        return result
    except Exception as e:
        logger.error("Interaction ingestion failed: %s", e)
        return {"error": str(e)}


def add_discovered_terms(phrases: Dict[str, str], source: str = "manual") -> Dict[str, Any]:
    """
    Manually add new terms to the engine (e.g. from admin panel).

    Args:
        phrases: {"blue hydrogen": "INDUSTRY_TERM", "ladder logic": "INDUSTRIAL_SKILL"}
        source: where the terms came from

    Returns:
        Summary of what was added
    """
    from services.ai_engine.collocation_engine import collocation_engine

    result = collocation_engine.add_runtime_phrases(phrases, source=source)

    # Persist immediately for manual additions
    collocation_engine.persist_learned_phrases()

    return result


def get_all_gazetteers() -> Dict[str, Any]:
    """
    Get a summary of all loaded gazetteers for the admin dashboard.
    """
    from services.ai_engine.collocation_engine import collocation_engine

    return {
        "stats": collocation_engine.get_learning_stats(),
        "categories": {
            label: {
                "count": len(terms),
                "sample": terms[:10],
            }
            for label, terms in collocation_engine.gazetteers.items()
        },
    }
