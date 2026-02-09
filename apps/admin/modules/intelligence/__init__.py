"""
Intelligence module for AI engines and analytics.
Provides complete AI intelligence system integration.
"""

from .intelligence_manager import (
    IntelligenceEngineManager,
    get_intelligence_manager,
    initialize_intelligence_engines
)

# Try to import enhanced engine if available
try:
    from .enhanced_engine import EnhancedIntelligenceEngine
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError:
    ENHANCED_ENGINE_AVAILABLE = False

# Try to import company intelligence if available  
try:
    from .company_intelligence import MarketIntelligenceEngine
    COMPANY_INTELLIGENCE_AVAILABLE = True
except ImportError:
    COMPANY_INTELLIGENCE_AVAILABLE = False

__all__ = [
    'IntelligenceEngineManager',
    'get_intelligence_manager',
    'initialize_intelligence_engines',
    'ENHANCED_ENGINE_AVAILABLE',
    'COMPANY_INTELLIGENCE_AVAILABLE'
]