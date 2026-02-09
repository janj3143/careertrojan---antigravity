"""services.admin_contracts

Central place for strict contracts used by admin pages.
"""

from __future__ import annotations

from typing import Final, List

PLAN_KEYS: Final[List[str]] = ["free", "monthly", "annual", "elitepro"]

# Web Company Intelligence contracts (admin backend must provide these keys)
WEB_INTEL_COMPANY_INDEX_KEYS: Final[List[str]] = ["companies"]
WEB_INTEL_COMPANY_RESULT_KEYS: Final[List[str]] = ["company_name", "confidence_score", "timestamp", "data_sources"]
WEB_INTEL_INDUSTRY_INDEX_KEYS: Final[List[str]] = ["industries"]
WEB_INTEL_INDUSTRY_ANALYSIS_KEYS: Final[List[str]] = ["industry", "timestamp", "data_sources"]
WEB_INTEL_COMPETITIVE_KEYS: Final[List[str]] = ["primary_company", "comparisons", "timestamp"]
WEB_INTEL_BULK_KEYS: Final[List[str]] = ["results", "timestamp"]