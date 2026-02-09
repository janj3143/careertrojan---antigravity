"""
IntelliCV-AI Company Intelligence Package

This package provides modular, production-grade company intelligence and enrichment tools for the IntelliCV platform.

Modules:
- nlp_extraction: AI/NLP entity extraction (spaCy)
- semantic_enrichment: Embedding generation
- json_schema: JSON schema validation and auto-population
- knowledge_graph: Company knowledge graph builder
- sentiment_analysis: Sentiment and reputation analysis
- data_quality: Data quality and anomaly detection
- feedback_learning: Feedback and continuous learning
- api_integration: API and dashboard integration

Main API:
- CompanyIntel: Robust, safe, and scalable company enrichment (see market_intelligence.py)
"""

from .nlp_extraction import extract_entities
# ...other imports as modules are implemented...

# Optionally, expose CompanyIntel if placed here or importable from market_intelligence.py
# from .company_intelligence import CompanyIntel
