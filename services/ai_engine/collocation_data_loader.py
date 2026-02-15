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
    Initialize the collocation engine with all gazetteer data,
    AND the term evolution engine for nomenclature lineage tracking.
    Should be called once at application startup.

    Args:
        sync_local: whether to copy gazetteers from L: to local C: drive

    Returns:
        Engine learning stats after initialization
    """
    from services.ai_engine.collocation_engine import collocation_engine

    # Load all gazetteer JSON files from the gazetteers/ folder
    loaded = collocation_engine.load_gazetteers()

    # Load term evolution chains (MRP→ERP, Basel I→III, etc.)
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine
        evo_stats = evolution_engine.get_stats()
        logger.info(
            "Term evolution engine loaded: %d chains, %d lineage terms, %d domains",
            evo_stats["chains_loaded"],
            evo_stats["total_lineage_terms"],
            len(evo_stats["domains"]),
        )
    except Exception as e:
        logger.warning("Term evolution engine failed to load (non-fatal): %s", e)

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
    Process a user login event for collocation learning AND evolution detection.
    Call this from auth middleware or the login endpoint.

    Now also:
    - Detects evolution patterns (user CV says "MRP", searching for "ERP")
    - Surfaces career evolution paths based on user's existing skills
    - Records potential new evolution links for future chain building

    Args:
        user_data: dict with keys like:
            - "skills": ["Machine Learning", "Data Analysis", ...]
            - "job_title": "Senior Process Engineer"
            - "industry": "Oil & Gas"
            - "cv_text": "Full resume text..."
            - "recent_searches": ["PLC engineer Houston", ...]
            - "bio": "Profile bio text..."

    Returns:
        Enrichment result summary including evolution insights
    """
    from services.ai_engine.collocation_engine import collocation_engine

    result = {}

    # Standard collocation enrichment
    try:
        result["collocation"] = collocation_engine.on_user_login(user_data)
    except Exception as e:
        logger.error("User login collocation enrichment failed: %s", e)
        result["collocation"] = {"error": str(e)}

    # Evolution pattern detection
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine

        skills = user_data.get("skills", [])
        job_titles = [user_data.get("job_title", "")] if user_data.get("job_title") else []
        searches = user_data.get("recent_searches", [])

        # Find evolution paths based on user's skills
        if skills:
            evolution_paths = evolution_engine.find_user_evolution_paths(
                user_skills=skills,
                user_job_titles=job_titles,
            )
            result["evolution_paths"] = evolution_paths[:5]  # Top 5 relevant chains

        # Detect CV → search evolution patterns
        if skills and searches:
            cv_terms = skills + job_titles
            patterns = evolution_engine.detect_evolution_patterns(
                user_cv_terms=cv_terms,
                user_search_terms=searches,
            )
            result["evolution_patterns"] = patterns

        # Find cross-domain bridge opportunities
        if skills:
            overlaps = evolution_engine.find_domain_overlaps(skills)
            result["domain_bridges"] = overlaps[:3]  # Top 3 bridges

    except Exception as e:
        logger.debug("Evolution enrichment skipped: %s", e)

    logger.info("User login enrichment complete: %s", {k: type(v).__name__ for k, v in result.items()})
    return result


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


# ── Term Evolution API (for AI engine + API endpoints) ───────────────────

def resolve_term_evolution(term: str) -> Optional[Dict[str, Any]]:
    """
    Look up the evolution chain for any industry term.
    Used by the AI engine when analyzing CVs/job descriptions.

    Example:
        resolve_term_evolution("MRP")
        → {"chain_id": "mrp_to_erp", "lineage": [...], "career_insight": "..."}
    """
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine
        return evolution_engine.resolve(term)
    except Exception as e:
        logger.debug("Evolution resolve failed for '%s': %s", term, e)
        return None


def get_evolution_context_for_ai(term: str) -> str:
    """
    Get a formatted text block about term evolution, suitable for
    injection into LLM prompts. Gives the AI context about nomenclature
    history and career transition paths.

    Example:
        context = get_evolution_context_for_ai("Basel II")
        # → "📊 TERM EVOLUTION CONTEXT: Basel III\nLineage: Basel I → II → III..."
    """
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine
        return evolution_engine.format_for_ai_context(term)
    except Exception as e:
        logger.debug("Evolution context failed for '%s': %s", term, e)
        return ""


def get_transferable_skills(term: str) -> list:
    """
    Get skills that transfer across an evolution chain.
    Used by the career advisor to suggest skill pivots.
    """
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine
        return evolution_engine.get_transferable_skills(term)
    except Exception as e:
        logger.debug("Transferable skills lookup failed for '%s': %s", term, e)
        return []


def get_evolution_stats() -> Dict[str, Any]:
    """
    Get evolution engine statistics for admin dashboard.
    """
    try:
        from services.ai_engine.term_evolution_engine import evolution_engine
        return evolution_engine.get_stats()
    except Exception as e:
        return {"error": str(e), "chains_loaded": 0}
