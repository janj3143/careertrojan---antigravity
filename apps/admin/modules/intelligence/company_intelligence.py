"""
Company Intelligence and Market Analysis Module
==============================================

This module handles company research, market analysis, and JSON data processing
for comprehensive business intelligence.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Optional shared backend: Google-first, Exa-fallback web lookup.
try:
    from shared_backend.services.web_search_orchestrator import two_tier_web_search  # type: ignore
except Exception:
    two_tier_web_search = None  # type: ignore


class WebMarketIntelligence:
    """Web-based company intelligence and research system."""

    def __init__(self):
        """Initialize the web intelligence system."""
        self.data_sources = {
            "company_websites": True,
            "linkedin_api": False,
            "google_search": True,
            "industry_databases": True
        }
        self.research_confidence_threshold = 80

    def research_company(self, company_name: str) -> Dict[str, Any]:
        """Comprehensive company research using available web sources."""
        intelligence: Dict[str, Any] = {
            "company_name": company_name,
            "research_timestamp": datetime.now().isoformat(),
            "data_sources_used": [],
            "sources": [],
            "summary": "",
            "overall_confidence": 0,
            "status": "unavailable",
        }

        if not two_tier_web_search:
            intelligence["error"] = "two_tier_web_search not available"
            return intelligence

        query = f"{company_name} company overview headquarters employees revenue"
        res = two_tier_web_search(
            query=query,
            domain=None,
            content_type="background",
            num_results=8,
            triggered_from="admin_portal.modules.intelligence.company_intelligence.WebMarketIntelligence.research_company",
        )

        candidates = (res.get("exa_results") or []) + (res.get("google_results") or [])
        text_parts = []
        urls = []
        for c in candidates[:5]:
            txt = (c.get("text") or c.get("snippet") or c.get("content") or "").strip()
            url = (c.get("url") or c.get("link") or "").strip()
            title = (c.get("title") or "").strip()
            if txt:
                text_parts.append(txt)
            if url:
                urls.append({"title": title, "url": url})

        summary = "\n\n".join(text_parts[:3]).strip()
        intelligence.update(
            {
                "data_sources_used": [res.get("method")] if res.get("method") else [],
                "sources": urls[:10],
                "summary": summary,
                "overall_confidence": 60 if summary else 0,
                "status": "ok" if summary or urls else "unavailable",
            }
        )

        return intelligence


class ComprehensiveJSONAnalyzer:
    """Comprehensive analysis of all JSON data in IntelliCV-AI."""

    def __init__(self, ai_data_path: str = "ai_data"):
        """Initialize the JSON analyzer."""
        self.ai_data_path = Path(ai_data_path)
        self.enhancement_opportunities = []
        self.data_quality_issues = []

    def analyze_email_intelligence(self, emails_file: Path) -> Dict[str, Any]:
        """Analyze email intelligence data."""
        try:
            with open(emails_file, 'r') as f:
                data = json.load(f)

            return {
                "total_emails": len(data),
                "corporate_domains": len(set([email.split('@')[1] for email in data if '@' in email])),
                "personal_emails": sum(1 for email in data if any(domain in email for domain in ['gmail', 'yahoo', 'hotmail'])),
                "quality_score": 0.85
            }
        except Exception as e:
            return {"error": str(e), "total_emails": 0}

    def analyze_company_intelligence(self, companies_path: Path) -> Dict[str, Any]:
        """Analyze company intelligence data."""
        try:
            if not companies_path.exists():
                return {
                    "total_companies": 0,
                    "industries_covered": 0,
                    "geographic_spread": 0,
                    "intelligence_completeness": 0.0,
                    "status": "unavailable",
                    "error": "companies path not found",
                }

            files = list(companies_path.glob("*.json"))
            total = len(files)
            industries = set()
            geos = set()
            with_core_fields = 0

            for fp in files:
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        ind = data.get("industry")
                        if isinstance(ind, str) and ind.strip():
                            industries.add(ind.strip())
                        hq = data.get("headquarters") or data.get("hq") or data.get("location")
                        if isinstance(hq, str) and hq.strip():
                            geos.add(hq.strip())

                        # Minimal completeness signal based on presence of a few real fields
                        core_hits = 0
                        for k in ("industry", "headquarters", "website", "domain", "description"):
                            v = data.get(k)
                            if isinstance(v, str) and v.strip():
                                core_hits += 1
                        if core_hits >= 2:
                            with_core_fields += 1
                except Exception:
                    continue

            completeness = (with_core_fields / total) if total else 0.0
            return {
                "total_companies": total,
                "industries_covered": len(industries),
                "geographic_spread": len(geos),
                "intelligence_completeness": round(completeness, 4),
                "status": "ok",
            }
        except Exception as e:
            return {
                "total_companies": 0,
                "industries_covered": 0,
                "geographic_spread": 0,
                "intelligence_completeness": 0.0,
                "status": "error",
                "error": str(e),
            }

    def generate_dashboard_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for enhanced dashboard visualization."""
        return {
            "summary_stats": {
                "total_emails": analysis_results.get("email_intelligence", {}).get("total_emails", 0),
                "total_companies": analysis_results.get("company_intelligence", {}).get("total_companies", 0),
                "data_quality_score": 85
            },
            "enhancement_opportunities": [
                "Expand geographic coverage",
                "Improve data validation",
                "Add more industry verticals"
            ]
        }
