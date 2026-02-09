"""
Web Intelligence Service for IntelliCV Admin Portal
Provides real web-based company research and competitive intelligence
"""

import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import time

# Optional shared backend: Google-first, Exa-fallback search.
try:
    from shared_backend.services.web_search_orchestrator import two_tier_web_search as _two_tier_web_search  # type: ignore
except Exception:
    _two_tier_web_search = None

class WebIntelligenceService:
    """Service to perform real web-based company research and intelligence gathering"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.api_keys = self._load_api_keys()
        self.rate_limit_delay = 1  # seconds between requests

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from configuration"""
        api_keys = {}

        # Check for API keys in config files
        config_files = [
            Path("./config/api_keys.json"),
            Path("./api_keys.json"),
            Path("./.env")
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    if config_file.suffix == '.json':
                        with open(config_file, 'r') as f:
                            data = json.load(f)
                            api_keys.update(data)
                    elif config_file.suffix == '.env':
                        with open(config_file, 'r') as f:
                            for line in f:
                                if '=' in line and not line.startswith('#'):
                                    key, value = line.strip().split('=', 1)
                                    api_keys[key] = value.strip('"\'')
                except Exception as e:
                    continue

        return api_keys

    def search_company_basic(self, company_name: str) -> Dict[str, Any]:
        """Perform basic company search using web scraping"""
        try:
            # Construct search query
            search_query = f"{company_name} company"
            search_url = f"https://www.google.com/search?q={search_query}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            # Parse search results
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract basic information from search results
            search_results = []
            result_divs = soup.find_all('div', class_=['g', 'result'])

            for div in result_divs[:5]:  # First 5 results
                try:
                    title_elem = div.find('h3')
                    link_elem = div.find('a')
                    snippet_elem = div.find('span', class_=['st', 'VwiC3b'])

                    if title_elem and link_elem:
                        result = {
                            'title': title_elem.get_text(),
                            'url': link_elem.get('href', ''),
                            'snippet': snippet_elem.get_text() if snippet_elem else ''
                        }
                        search_results.append(result)
                except Exception:
                    continue

            # Extract potential company information
            company_info = {
                'company_name': company_name,
                'search_results': search_results,
                'search_timestamp': datetime.now().isoformat(),
                'confidence_score': len(search_results) * 10  # Basic confidence scoring
            }

            # If scraping yields nothing, attempt shared Google→Exa fallback.
            if not search_results and _two_tier_web_search:
                try:
                    fallback = _two_tier_web_search(
                        query=search_query,
                        content_type="background",
                        num_results=5,
                        triggered_from="admin_portal.services.web_intelligence_service.search_company_basic",
                    )
                    candidates = (fallback.get("google_results") or []) + (fallback.get("exa_results") or [])
                    normalized = []
                    for item in candidates[:5]:
                        url = item.get("url") or item.get("link")
                        if not url:
                            continue
                        normalized.append(
                            {
                                "title": item.get("title") or item.get("name") or "",
                                "url": url,
                                "snippet": item.get("snippet") or item.get("text") or "",
                            }
                        )
                    if normalized:
                        company_info["search_results"] = normalized
                        company_info["confidence_score"] = len(normalized) * 10
                        company_info["fallback_method"] = fallback.get("method")
                except Exception:
                    pass

            # Try to extract specific company details
            for result in search_results:
                snippet = result['snippet'].lower()

                # Look for industry information
                if 'industry' not in company_info and any(term in snippet for term in ['software', 'technology', 'finance', 'healthcare', 'manufacturing']):
                    if 'software' in snippet or 'technology' in snippet:
                        company_info['industry'] = 'Technology'
                    elif 'finance' in snippet or 'bank' in snippet:
                        company_info['industry'] = 'Finance'
                    elif 'healthcare' in snippet or 'medical' in snippet:
                        company_info['industry'] = 'Healthcare'
                    elif 'manufacturing' in snippet:
                        company_info['industry'] = 'Manufacturing'

                # Look for location information
                if 'location' not in company_info:
                    # Simple location extraction
                    locations = ['california', 'new york', 'texas', 'london', 'singapore', 'toronto']
                    for loc in locations:
                        if loc in snippet:
                            company_info['location'] = loc.title()
                            break

            time.sleep(self.rate_limit_delay)  # Rate limiting
            return company_info

        except Exception as e:
            # Best-effort: if scraping fails, try shared fallback.
            if _two_tier_web_search:
                try:
                    fallback = _two_tier_web_search(
                        query=f"{company_name} company",
                        content_type="background",
                        num_results=5,
                        triggered_from="admin_portal.services.web_intelligence_service.search_company_basic",
                    )
                    candidates = (fallback.get("google_results") or []) + (fallback.get("exa_results") or [])
                    normalized = []
                    for item in candidates[:5]:
                        url = item.get("url") or item.get("link")
                        if not url:
                            continue
                        normalized.append(
                            {
                                "title": item.get("title") or item.get("name") or "",
                                "url": url,
                                "snippet": item.get("snippet") or item.get("text") or "",
                            }
                        )
                    return {
                        "company_name": company_name,
                        "search_results": normalized,
                        "search_timestamp": datetime.now().isoformat(),
                        "confidence_score": len(normalized) * 10,
                        "error": f"Search failed: {str(e)}",
                        "fallback_method": fallback.get("method"),
                    }
                except Exception:
                    pass

            return {
                'company_name': company_name,
                'error': f"Search failed: {str(e)}",
                'confidence_score': 0,
                'search_timestamp': datetime.now().isoformat()
            }

    def analyze_company_website(self, company_url: str) -> Dict[str, Any]:
        """Analyze company website for intelligence"""
        try:
            response = self.session.get(company_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            analysis = {
                'url': company_url,
                'title': soup.title.get_text() if soup.title else 'No title',
                'description': '',
                'technologies': [],
                'contact_info': {},
                'social_links': [],
                'analysis_timestamp': datetime.now().isoformat()
            }

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                analysis['description'] = meta_desc.get('content', '')

            # Look for technology indicators
            page_text = soup.get_text().lower()
            tech_keywords = {
                'AI/ML': ['artificial intelligence', 'machine learning', 'ai', 'ml', 'deep learning'],
                'Cloud': ['aws', 'azure', 'google cloud', 'cloud computing'],
                'Web Technologies': ['react', 'angular', 'vue', 'javascript', 'node.js'],
                'Data': ['big data', 'analytics', 'database', 'data science'],
                'Mobile': ['mobile app', 'ios', 'android', 'mobile development']
            }

            for category, keywords in tech_keywords.items():
                if any(keyword in page_text for keyword in keywords):
                    analysis['technologies'].append(category)

            # Extract contact information
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            phone_pattern = r'[\+]?[1-9]?[\d\s\-\(\)]{10,15}'

            import re
            emails = re.findall(email_pattern, page_text)
            phones = re.findall(phone_pattern, page_text)

            if emails:
                analysis['contact_info']['emails'] = list(set(emails))[:3]  # First 3 unique emails
            if phones:
                analysis['contact_info']['phones'] = list(set(phones))[:2]  # First 2 unique phones

            # Extract social media links
            social_platforms = ['linkedin', 'twitter', 'facebook', 'instagram']
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href'].lower()
                for platform in social_platforms:
                    if platform in href:
                        analysis['social_links'].append({
                            'platform': platform,
                            'url': link['href']
                        })

            time.sleep(self.rate_limit_delay)  # Rate limiting
            return analysis

        except Exception as e:
            return {
                'url': company_url,
                'error': f"Website analysis failed: {str(e)}",
                'analysis_timestamp': datetime.now().isoformat()
            }

    def search_company_news(self, company_name: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Search for recent news about a company"""
        try:
            # Basic news search using Google News approach
            news_query = f"{company_name} news"
            search_url = f"https://www.google.com/search?q={news_query}&tbm=nws"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Parse news results
            news_divs = soup.find_all('div', class_=['g', 'result'])

            for div in news_divs[:10]:  # First 10 news items
                try:
                    title_elem = div.find('h3')
                    link_elem = div.find('a')
                    source_elem = div.find('span', class_=['f', 'source'])
                    date_elem = div.find('span', class_=['f', 'nsa'])

                    if title_elem and link_elem:
                        news_item = {
                            'title': title_elem.get_text(),
                            'url': link_elem.get('href', ''),
                            'source': source_elem.get_text() if source_elem else 'Unknown',
                            'date': date_elem.get_text() if date_elem else 'Unknown'
                        }
                        news_items.append(news_item)
                except Exception:
                    continue

            # If scraping yields nothing, attempt shared Google→Exa fallback.
            if not news_items and _two_tier_web_search:
                try:
                    fallback = _two_tier_web_search(
                        query=f"{company_name} news",
                        content_type="generic",
                        num_results=10,
                        triggered_from="admin_portal.services.web_intelligence_service.search_company_news",
                    )
                    candidates = (fallback.get("google_results") or []) + (fallback.get("exa_results") or [])
                    normalized = []
                    for item in candidates[:10]:
                        url = item.get("url") or item.get("link")
                        if not url:
                            continue
                        normalized.append(
                            {
                                "title": item.get("title") or item.get("name") or "",
                                "url": url,
                                "source": "exa" if item.get("source") == "exa" else "web",
                                "date": "Unknown",
                            }
                        )
                    if normalized:
                        news_items = normalized
                except Exception:
                    pass

            time.sleep(self.rate_limit_delay)  # Rate limiting
            return news_items

        except Exception as e:
            if _two_tier_web_search:
                try:
                    fallback = _two_tier_web_search(
                        query=f"{company_name} news",
                        content_type="generic",
                        num_results=10,
                        triggered_from="admin_portal.services.web_intelligence_service.search_company_news",
                    )
                    candidates = (fallback.get("google_results") or []) + (fallback.get("exa_results") or [])
                    normalized = []
                    for item in candidates[:10]:
                        url = item.get("url") or item.get("link")
                        if not url:
                            continue
                        normalized.append(
                            {
                                "title": item.get("title") or item.get("name") or "",
                                "url": url,
                                "source": "exa" if item.get("source") == "exa" else "web",
                                "date": "Unknown",
                                "error": f"News search failed: {str(e)}",
                            }
                        )
                    return normalized or [{'error': f"News search failed: {str(e)}"}]
                except Exception:
                    pass

            return [{'error': f"News search failed: {str(e)}"}]

    def get_competitor_analysis(self, company_name: str, industry: str) -> Dict[str, Any]:
        """Get competitive analysis for a company"""
        try:
            # Search for competitors
            competitor_query = f"{company_name} competitors {industry}"
            search_url = f"https://www.google.com/search?q={competitor_query}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract competitor information
            competitors = []
            search_text = soup.get_text().lower()

            # Common competitor indicators
            competitor_phrases = [
                'competitors include', 'similar to', 'alternative to',
                'competes with', 'vs', 'compared to'
            ]

            # Look for potential competitor mentions
            for phrase in competitor_phrases:
                if phrase in search_text:
                    # Extract text around the phrase
                    phrase_index = search_text.find(phrase)
                    context = search_text[phrase_index:phrase_index+200]

                    # Simple extraction of potential company names
                    words = context.split()
                    for word in words:
                        if len(word) > 3 and word.isupper():  # Likely company acronym
                            competitors.append(word)

            competitive_analysis = {
                'company': company_name,
                'industry': industry,
                'potential_competitors': list(set(competitors))[:10],  # Remove duplicates, limit to 10
                'analysis_method': 'web_search',
                'analysis_timestamp': datetime.now().isoformat(),
                'confidence': 'medium'  # Web search has medium confidence
            }

            time.sleep(self.rate_limit_delay)  # Rate limiting
            return competitive_analysis

        except Exception as e:
            return {
                'company': company_name,
                'error': f"Competitor analysis failed: {str(e)}",
                'analysis_timestamp': datetime.now().isoformat()
            }

    def validate_company_exists(self, company_name: str) -> Dict[str, Any]:
        """Validate if a company exists and get basic verification"""
        try:
            # Simple existence check via search
            basic_search = self.search_company_basic(company_name)

            # Check if search returned meaningful results
            has_results = len(basic_search.get('search_results', [])) > 0
            confidence_score = basic_search.get('confidence_score', 0)

            # Additional validation checks
            validation = {
                'company_name': company_name,
                'exists': has_results,
                'confidence_score': confidence_score,
                'validation_timestamp': datetime.now().isoformat(),
                'verification_method': 'web_search'
            }

            if has_results:
                validation['status'] = 'verified' if confidence_score > 30 else 'likely_exists'
                validation['search_results_count'] = len(basic_search.get('search_results', []))
            else:
                validation['status'] = 'not_found'
                validation['note'] = 'Company not found in web search results'

            return validation

        except Exception as e:
            return {
                'company_name': company_name,
                'exists': False,
                'error': f"Validation failed: {str(e)}",
                'validation_timestamp': datetime.now().isoformat()
            }

    def get_industry_intelligence(self, industry: str) -> Dict[str, Any]:
        """Get intelligence about an industry"""
        try:
            # Search for industry information
            industry_query = f"{industry} industry trends market size growth"
            search_url = f"https://www.google.com/search?q={industry_query}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract industry insights
            industry_intelligence = {
                'industry': industry,
                'search_timestamp': datetime.now().isoformat(),
                'insights': [],
                'trends': [],
                'key_players': []
            }

            # Look for trend keywords
            page_text = soup.get_text().lower()
            trend_keywords = ['growth', 'decline', 'increasing', 'decreasing', 'emerging', 'disruption']

            for keyword in trend_keywords:
                if keyword in page_text:
                    industry_intelligence['trends'].append(keyword)

            # Extract search results for insights
            result_divs = soup.find_all('div', class_=['g', 'result'])

            for div in result_divs[:5]:
                try:
                    snippet_elem = div.find('span', class_=['st', 'VwiC3b'])
                    if snippet_elem:
                        snippet = snippet_elem.get_text()
                        if len(snippet) > 50:  # Only meaningful snippets
                            industry_intelligence['insights'].append(snippet)
                except Exception:
                    continue

            time.sleep(self.rate_limit_delay)
            return industry_intelligence

        except Exception as e:
            return {
                'industry': industry,
                'error': f"Industry intelligence failed: {str(e)}",
                'search_timestamp': datetime.now().isoformat()
            }

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of web intelligence services"""
        return {
            'service_name': 'WebIntelligenceService',
            'status': 'active',
            'api_keys_loaded': len(self.api_keys),
            'available_methods': [
                'search_company_basic',
                'analyze_company_website',
                'search_company_news',
                'get_competitor_analysis',
                'validate_company_exists',
                'get_industry_intelligence'
            ],
            'rate_limit_delay': self.rate_limit_delay,
            'last_check': datetime.now().isoformat()
        }
