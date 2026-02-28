"""
Company Intelligence Service for Interview Preparation
======================================================

Provides company research for interview preparation:
- Company overview (what they do, industry, size)
- Hiring history (have they hired similar roles, when)
- Recent news, appointments, product launches
- Key highlights and talking points

Wraps the existing company_intelligence module and adds
interview-prep-specific features.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("careertrojan.company_intel")


class CompanyIntelService:
    """
    Service for gathering company intelligence for interview preparation.
    
    Provides:
    - Company overview and background
    - Hiring history for similar roles
    - Recent news and developments
    - Key highlights for interview talking points
    """

    def __init__(self):
        self._web_intel = None
        self._company_parser = None
        self._web_search = None

    def _get_web_intel(self):
        """Lazy-load web intelligence module."""
        if self._web_intel is None:
            try:
                from services.backend_api.services.company_intelligence.enrich import enrich_company
                self._web_intel = enrich_company
            except ImportError:
                logger.warning("Company intelligence enrich module not available")
        return self._web_intel

    def _get_web_search(self):
        """Lazy-load web search orchestrator."""
        if self._web_search is None:
            try:
                from shared_backend.services.web_search_orchestrator import two_tier_web_search
                self._web_search = two_tier_web_search
            except ImportError:
                logger.warning("Web search orchestrator not available")
        return self._web_search

    async def get_company_overview(self, company_name: str) -> Dict[str, Any]:
        """
        Get comprehensive company overview for interview prep.
        
        Args:
            company_name: Name of the target company
            
        Returns:
            Dict with company overview, industry, description, website
        """
        overview = {
            "company_name": company_name,
            "research_timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "description": "",
            "industry": "",
            "website": "",
            "logo_url": "",
            "key_facts": [],
            "sources": [],
        }

        # Try the company intelligence enrichment
        enrich_fn = self._get_web_intel()
        if enrich_fn:
            try:
                import requests
                session = requests.Session()
                session.headers.update({'User-Agent': 'Mozilla/5.0 (CareerTrojan/1.0)'})
                enriched = enrich_fn(company_name, session, {}, timeout=15)
                
                if enriched:
                    overview.update({
                        "description": enriched.get("description", ""),
                        "industry": enriched.get("industry", ""),
                        "website": enriched.get("website", ""),
                        "logo_url": enriched.get("logo_url", ""),
                        "status": "ok" if enriched.get("description") else "partial",
                    })
            except Exception as e:
                logger.warning(f"Company enrichment failed: {e}")

        # If no description yet, try web search
        if not overview["description"]:
            web_search = self._get_web_search()
            if web_search:
                try:
                    query = f"{company_name} company overview what they do products services"
                    result = web_search(
                        query=query,
                        domain=None,
                        content_type="background",
                        num_results=5,
                        triggered_from="company_intel_service.get_company_overview",
                    )
                    
                    candidates = (result.get("exa_results") or []) + (result.get("google_results") or [])
                    texts = []
                    for c in candidates[:3]:
                        txt = (c.get("text") or c.get("snippet") or c.get("content") or "").strip()
                        url = (c.get("url") or c.get("link") or "").strip()
                        if txt:
                            texts.append(txt)
                        if url:
                            overview["sources"].append({"url": url, "title": c.get("title", "")})
                    
                    if texts:
                        overview["description"] = "\n\n".join(texts[:2])
                        overview["status"] = "ok"
                except Exception as e:
                    logger.warning(f"Web search for overview failed: {e}")

        return overview

    async def get_hiring_history(
        self, 
        company_name: str, 
        role_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research if company has hired similar roles and when.
        
        Args:
            company_name: Target company name
            role_title: Optional specific role to search for
            
        Returns:
            Dict with hiring history, similar roles, timeline
        """
        history = {
            "company_name": company_name,
            "role_searched": role_title,
            "research_timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "similar_roles_found": [],
            "hiring_signals": [],
            "growth_indicators": [],
            "sources": [],
        }

        web_search = self._get_web_search()
        if not web_search:
            history["status"] = "unavailable"
            history["error"] = "Web search not configured"
            return history

        try:
            # Search for hiring history
            if role_title:
                query = f"{company_name} hiring {role_title} jobs careers team"
            else:
                query = f"{company_name} hiring jobs careers growth team expansion"
            
            result = web_search(
                query=query,
                domain=None,
                content_type="news",
                num_results=8,
                triggered_from="company_intel_service.get_hiring_history",
            )

            candidates = (result.get("exa_results") or []) + (result.get("google_results") or [])
            
            for c in candidates[:5]:
                txt = (c.get("text") or c.get("snippet") or c.get("content") or "").strip()
                url = (c.get("url") or c.get("link") or "").strip()
                title = (c.get("title") or "").strip()
                
                if txt:
                    # Look for hiring signals in the text
                    txt_lower = txt.lower()
                    if any(kw in txt_lower for kw in ["hiring", "job", "career", "position", "role", "team", "engineer", "manager"]):
                        history["hiring_signals"].append({
                            "snippet": txt[:300],
                            "source_url": url,
                            "source_title": title,
                        })
                    
                    # Look for growth indicators
                    if any(kw in txt_lower for kw in ["growth", "expand", "series", "funding", "revenue", "headcount"]):
                        history["growth_indicators"].append({
                            "snippet": txt[:300],
                            "source_url": url,
                        })
                
                if url:
                    history["sources"].append({"url": url, "title": title})

            history["status"] = "ok" if history["hiring_signals"] or history["growth_indicators"] else "no_data"
            
        except Exception as e:
            logger.warning(f"Hiring history search failed: {e}")
            history["status"] = "error"
            history["error"] = str(e)

        return history

    async def get_recent_news(
        self, 
        company_name: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Get recent company news, appointments, product launches.
        
        Args:
            company_name: Target company name
            days_back: How many days back to search (default 90)
            
        Returns:
            Dict with news items, appointments, product launches
        """
        news = {
            "company_name": company_name,
            "days_back": days_back,
            "research_timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "news_items": [],
            "appointments": [],
            "product_launches": [],
            "tech_developments": [],
            "sources": [],
        }

        web_search = self._get_web_search()
        if not web_search:
            news["status"] = "unavailable"
            news["error"] = "Web search not configured"
            return news

        try:
            # Search for recent news
            query = f"{company_name} news announcements 2026"
            result = web_search(
                query=query,
                domain=None,
                content_type="news",
                num_results=10,
                triggered_from="company_intel_service.get_recent_news",
            )

            candidates = (result.get("exa_results") or []) + (result.get("google_results") or [])
            
            for c in candidates:
                txt = (c.get("text") or c.get("snippet") or c.get("content") or "").strip()
                url = (c.get("url") or c.get("link") or "").strip()
                title = (c.get("title") or "").strip()
                
                if not txt:
                    continue
                    
                txt_lower = txt.lower()
                item = {
                    "title": title,
                    "snippet": txt[:400],
                    "url": url,
                }
                
                # Categorize the news
                if any(kw in txt_lower for kw in ["appoint", "ceo", "cto", "cfo", "vp", "director", "hire", "join", "promote"]):
                    news["appointments"].append(item)
                elif any(kw in txt_lower for kw in ["launch", "release", "announce", "new product", "unveil", "introduce"]):
                    news["product_launches"].append(item)
                elif any(kw in txt_lower for kw in ["technology", "ai", "machine learning", "platform", "infrastructure", "cloud"]):
                    news["tech_developments"].append(item)
                else:
                    news["news_items"].append(item)
                
                if url:
                    news["sources"].append({"url": url, "title": title})

            news["status"] = "ok" if any([
                news["news_items"], 
                news["appointments"], 
                news["product_launches"],
                news["tech_developments"]
            ]) else "no_data"
            
        except Exception as e:
            logger.warning(f"News search failed: {e}")
            news["status"] = "error"
            news["error"] = str(e)

        return news

    async def get_interview_talking_points(
        self,
        company_name: str,
        role_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate interview talking points based on company research.
        
        Combines overview, news, and hiring data into actionable
        talking points for an interview.
        
        Args:
            company_name: Target company name
            role_title: Optional role being interviewed for
            
        Returns:
            Dict with categorized talking points
        """
        # Gather all intel
        overview = await self.get_company_overview(company_name)
        news = await self.get_recent_news(company_name)
        hiring = await self.get_hiring_history(company_name, role_title)

        talking_points = {
            "company_name": company_name,
            "role_title": role_title,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "ok",
            
            # Company understanding points
            "company_understanding": [],
            
            # Recent developments to mention
            "recent_developments": [],
            
            # Questions to ask them
            "questions_to_ask": [],
            
            # Sources for fact-checking
            "sources": [],
        }

        # Generate company understanding points
        if overview.get("description"):
            talking_points["company_understanding"].append({
                "point": f"I understand {company_name} focuses on {overview.get('industry', 'their industry')}",
                "detail": overview["description"][:200],
            })

        # Add recent developments
        for item in (news.get("product_launches") or [])[:2]:
            talking_points["recent_developments"].append({
                "type": "product_launch",
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")[:150],
            })

        for item in (news.get("appointments") or [])[:2]:
            talking_points["recent_developments"].append({
                "type": "appointment",
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")[:150],
            })

        for item in (news.get("tech_developments") or [])[:2]:
            talking_points["recent_developments"].append({
                "type": "tech",
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")[:150],
            })

        # Generate questions to ask
        if news.get("product_launches"):
            talking_points["questions_to_ask"].append(
                f"I noticed {company_name} recently launched new products. How does this role contribute to those initiatives?"
            )

        if hiring.get("growth_indicators"):
            talking_points["questions_to_ask"].append(
                f"With {company_name}'s growth trajectory, what are the biggest challenges the team is facing?"
            )

        talking_points["questions_to_ask"].extend([
            f"What does success look like in this role in the first 90 days?",
            f"How does the team collaborate across departments?",
            f"What's the most exciting project the team is working on?",
        ])

        # Collect sources
        all_sources = (
            overview.get("sources", []) +
            news.get("sources", []) +
            hiring.get("sources", [])
        )
        seen_urls = set()
        for src in all_sources:
            url = src.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                talking_points["sources"].append(src)

        return talking_points

    async def get_full_company_intel(
        self,
        company_name: str,
        role_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete company intelligence package for interview prep.
        
        Combines all research into a single comprehensive report.
        
        Args:
            company_name: Target company name
            role_title: Optional role being interviewed for
            
        Returns:
            Complete company intelligence report
        """
        overview = await self.get_company_overview(company_name)
        hiring = await self.get_hiring_history(company_name, role_title)
        news = await self.get_recent_news(company_name)
        talking_points = await self.get_interview_talking_points(company_name, role_title)

        return {
            "company_name": company_name,
            "role_title": role_title,
            "generated_at": datetime.utcnow().isoformat(),
            "overview": overview,
            "hiring_history": hiring,
            "recent_news": news,
            "talking_points": talking_points,
            "status": "ok" if overview.get("status") == "ok" else "partial",
        }


# Singleton instance
company_intel_service = CompanyIntelService()
