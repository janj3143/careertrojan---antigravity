"""
Intelligence Hub Real Data Connector
===================================

Connects Intelligence Hub to real AI services and engines instead of demo data.
Provides comprehensive integration with:
- UnifiedAIEngine (Bayesian, NLP, LLM, Fuzzy, Fusion)
- RealAIConnector (34k+ CV database)
- Portal Bridge Intelligence Services
- Live system monitoring

Author: IntelliCV-AI Team
Date: November 11, 2025
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add shared_backend to path for portal bridge access
backend_path = Path(__file__).parent.parent.parent / "shared_backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

class IntelligenceHubConnector:
    """Real data connector for Intelligence Hub - NO MORE DEMO DATA!"""

    def __init__(self):
        self.unified_ai_engine = None
        self.real_ai_connector = None
        self.portal_bridge = None
        self.system_status = "initializing"

        # Initialize all real services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all real AI services and connectors"""

        # 1. Initialize UnifiedAIEngine
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from unified_ai_engine import get_unified_ai_engine
            self.unified_ai_engine = get_unified_ai_engine()
            logger.info("✅ UnifiedAIEngine initialized - Fusion AI available")
        except Exception as e:
            logger.warning(f"UnifiedAIEngine not available: {e}")

        # 2. Initialize RealAIConnector
        try:
            from services.real_ai_connector import get_real_ai_connector
            self.real_ai_connector = get_real_ai_connector()
            logger.info("✅ RealAIConnector initialized - 34k+ CV database connected")
        except Exception as e:
            logger.warning(f"RealAIConnector not available: {e}")

        # 3. Initialize Portal Bridge
        try:
            from services.portal_bridge import portal_bridge
            self.portal_bridge = portal_bridge
            logger.info("✅ Portal Bridge initialized - Cross-portal intelligence active")
        except Exception as e:
            logger.warning(f"Portal Bridge not available: {e}")

        # Update system status
        services_available = sum([
            self.unified_ai_engine is not None,
            self.real_ai_connector is not None,
            self.portal_bridge is not None
        ])

        if services_available == 3:
            self.system_status = "fully_operational"
        elif services_available >= 1:
            self.system_status = "partially_operational"
        else:
            self.system_status = "unavailable"

        logger.info(f"Intelligence Hub Status: {self.system_status} ({services_available}/3 services)")

    def get_real_service_metrics(self) -> Dict[str, Any]:
        """Get real service metrics from actual AI engines"""

        if self.system_status == "unavailable":
            return self._get_unavailable_metrics()

        metrics = {
            "service_health": {},
            "statistics": {"total": {"calls": 0, "success": 0, "errors": 0}},
            "performance": {"avg_response_time": 0, "memory_usage": 0},
            "engine_details": {},
            "data_source": "REAL_AI_ENGINES",
            "last_update": datetime.now().isoformat()
        }

        # Get UnifiedAI metrics
        if self.unified_ai_engine:
            try:
                ai_stats = self.unified_ai_engine.get_engine_statistics()
                metrics["engine_details"]["unified_ai"] = {
                    "status": "operational",
                    "bayesian_queries": ai_stats.get("bayesian_calls", 0),
                    "nlp_queries": ai_stats.get("nlp_calls", 0),
                    "fuzzy_queries": ai_stats.get("fuzzy_calls", 0),
                    "fusion_queries": ai_stats.get("fusion_calls", 0),
                    "total_ai_calls": ai_stats.get("total_calls", 0)
                }
                metrics["service_health"]["unified_ai"] = "healthy"
                metrics["statistics"]["total"]["calls"] += ai_stats.get("total_calls", 0)
            except Exception as e:
                logger.error(f"Error getting UnifiedAI metrics: {e}")
                metrics["service_health"]["unified_ai"] = "error"

        # Get RealAI metrics
        if self.real_ai_connector:
            try:
                real_stats = self.real_ai_connector.get_connection_stats()
                metrics["engine_details"]["real_ai"] = {
                    "status": "operational",
                    "cvs_processed": real_stats.get("total_cvs", 0),
                    "patterns_analyzed": real_stats.get("patterns_found", 0),
                    "skills_extracted": real_stats.get("unique_skills", 0),
                    "companies_mapped": real_stats.get("unique_companies", 0)
                }
                metrics["service_health"]["real_ai"] = "healthy"
                metrics["statistics"]["total"]["success"] += real_stats.get("successful_queries", 0)
            except Exception as e:
                logger.error(f"Error getting RealAI metrics: {e}")
                metrics["service_health"]["real_ai"] = "error"

        # Get Portal Bridge metrics
        if self.portal_bridge:
            try:
                bridge_health = self.portal_bridge.health_check()
                metrics["engine_details"]["portal_bridge"] = bridge_health
                metrics["service_health"]["portal_bridge"] = "healthy" if bridge_health.get("status") == "healthy" else "warning"
            except Exception as e:
                logger.error(f"Error getting Portal Bridge metrics: {e}")
                metrics["service_health"]["portal_bridge"] = "error"

        # Calculate overall success rate
        total_calls = metrics["statistics"]["total"]["calls"]
        if total_calls > 0:
            success_rate = (metrics["statistics"]["total"]["success"] / total_calls) * 100
            metrics["overall_success_rate"] = f"{success_rate:.1f}%"
        else:
            metrics["overall_success_rate"] = "0.0%"

        return metrics

    def get_ai_engine_details(self, engine_type: str) -> Dict[str, Any]:
        """Get detailed information about specific AI engine"""

        if engine_type == "unified" and self.unified_ai_engine:
            try:
                engine_info = self.unified_ai_engine.get_detailed_status()
                return {
                    "status": "operational",
                    "engines": {
                        "bayesian": engine_info.get("bayesian_engine", {}),
                        "nlp": engine_info.get("nlp_engine", {}),
                        "fuzzy": engine_info.get("fuzzy_engine", {}),
                        "llm": engine_info.get("llm_engine", {}),
                        "fusion": engine_info.get("fusion_engine", {})
                    },
                    "performance": engine_info.get("performance_metrics", {}),
                    "data_source": "unified_ai_engine"
                }
            except Exception as e:
                logger.error(f"Error getting unified AI details: {e}")
                return {"status": "error", "error": str(e)}

        elif engine_type == "real_data" and self.real_ai_connector:
            try:
                connector_info = self.real_ai_connector.get_detailed_analytics()
                return {
                    "status": "operational",
                    "database_info": connector_info.get("database_stats", {}),
                    "processing_info": connector_info.get("processing_stats", {}),
                    "data_quality": connector_info.get("data_quality_metrics", {}),
                    "data_source": "real_ai_connector_34k_cvs"
                }
            except Exception as e:
                logger.error(f"Error getting real AI details: {e}")
                return {"status": "error", "error": str(e)}

        elif engine_type == "fusion":
            # Fusion is part of unified engine
            return self.get_fusion_engine_status()

        return {"status": "not_available", "message": f"Engine {engine_type} not initialized"}

    def get_fusion_engine_status(self) -> Dict[str, Any]:
        """Get detailed fusion engine status - the core AI fusion capability"""

        if not self.unified_ai_engine:
            return {"status": "not_available", "message": "UnifiedAIEngine not initialized"}

        try:
            fusion_status = self.unified_ai_engine.get_fusion_engine_status()
            return {
                "status": "operational",
                "fusion_capabilities": {
                    "bayesian_nlp_fusion": fusion_status.get("bayesian_nlp", False),
                    "fuzzy_llm_fusion": fusion_status.get("fuzzy_llm", False),
                    "all_engine_fusion": fusion_status.get("full_fusion", False),
                    "adaptive_weighting": fusion_status.get("adaptive_weights", False)
                },
                "fusion_queries_today": fusion_status.get("fusion_queries", 0),
                "fusion_accuracy": fusion_status.get("fusion_accuracy", 0.0),
                "combined_engines": fusion_status.get("engines_combined", []),
                "data_source": "unified_ai_fusion_engine"
            }
        except Exception as e:
            logger.error(f"Error getting fusion status: {e}")
            return {"status": "error", "error": str(e)}

    def get_real_analytics_data(self) -> Dict[str, Any]:
        """Get real analytics data instead of demo placeholders"""

        analytics = {
            "data_processing": {},
            "intelligence_patterns": {},
            "system_performance": {},
            "data_source": "REAL_ANALYTICS"
        }

        # Real AI Connector analytics
        if self.real_ai_connector:
            try:
                real_analytics = self.real_ai_connector.get_comprehensive_analytics()
                analytics["data_processing"] = {
                    "total_cvs_processed": real_analytics.get("total_files", 0),
                    "unique_skills_found": len(real_analytics.get("all_skills", [])),
                    "companies_identified": len(real_analytics.get("all_companies", [])),
                    "job_titles_normalized": len(real_analytics.get("job_titles", [])),
                    "patterns_discovered": real_analytics.get("pattern_count", 0)
                }
            except Exception as e:
                logger.error(f"Error getting real analytics: {e}")

        # UnifiedAI analytics
        if self.unified_ai_engine:
            try:
                ai_analytics = self.unified_ai_engine.get_learning_analytics()
                analytics["intelligence_patterns"] = {
                    "learning_instances": ai_analytics.get("total_learnings", 0),
                    "pattern_recognition_rate": ai_analytics.get("pattern_accuracy", 0.0),
                    "adaptive_improvements": ai_analytics.get("adaptations", 0),
                    "fusion_operations": ai_analytics.get("fusion_count", 0)
                }
            except Exception as e:
                logger.error(f"Error getting AI analytics: {e}")

        return analytics

    def _get_unavailable_metrics(self) -> Dict[str, Any]:
        """Return explicit unavailable metrics when no real services are connected."""
        return {
            "service_health": {
                "unified_ai": "unavailable",
                "real_ai": "unavailable",
                "portal_bridge": "unavailable",
            },
            "statistics": {"total": {"calls": None, "success": None, "errors": None}},
            "performance": {"avg_response_time": None, "memory_usage": None},
            "engine_details": {},
            "data_source": "UNAVAILABLE_NO_SERVICES",
            "warning": "Real AI services are not connected; no demo/mock metrics are shown.",
            "last_update": datetime.now().isoformat(),
        }

    def test_all_connections(self) -> Dict[str, Any]:
        """Test all AI service connections"""

        test_results = {
            "unified_ai": "not_tested",
            "real_ai": "not_tested",
            "portal_bridge": "not_tested",
            "fusion_engine": "not_tested",
            "overall_status": "unknown"
        }

        # Test UnifiedAI
        if self.unified_ai_engine:
            try:
                test_data = {"test": "connection", "timestamp": datetime.now().isoformat()}
                result = self.unified_ai_engine.quick_health_check()
                test_results["unified_ai"] = "operational" if result.get("status") == "healthy" else "error"
            except Exception as e:
                test_results["unified_ai"] = f"error: {str(e)}"

        # Test RealAI
        if self.real_ai_connector:
            try:
                stats = self.real_ai_connector.get_connection_stats()
                test_results["real_ai"] = "operational" if stats.get("status") == "connected" else "warning"
            except Exception as e:
                test_results["real_ai"] = f"error: {str(e)}"

        # Test Portal Bridge
        if self.portal_bridge:
            try:
                health = self.portal_bridge.health_check()
                test_results["portal_bridge"] = "operational" if health.get("status") == "healthy" else "warning"
            except Exception as e:
                test_results["portal_bridge"] = f"error: {str(e)}"

        # Test Fusion specifically
        fusion_status = self.get_fusion_engine_status()
        test_results["fusion_engine"] = fusion_status.get("status", "not_available")

        # Overall status
        operational_count = sum(1 for status in test_results.values() if status == "operational")
        if operational_count >= 3:
            test_results["overall_status"] = "fully_operational"
        elif operational_count >= 1:
            test_results["overall_status"] = "partially_operational"
        else:
            test_results["overall_status"] = "unavailable"

        test_results["test_timestamp"] = datetime.now().isoformat()

        return test_results


# Global instance
_intelligence_hub_connector = None

def get_intelligence_hub_connector():
    """Get or create the global intelligence hub connector instance"""
    global _intelligence_hub_connector
    if _intelligence_hub_connector is None:
        _intelligence_hub_connector = IntelligenceHubConnector()
    return _intelligence_hub_connector
