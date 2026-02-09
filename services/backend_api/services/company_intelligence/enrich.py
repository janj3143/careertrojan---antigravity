"""
Company enrichment logic (web/API enrichment, logo, industry)
"""
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Dict
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import LOGOS_DIR
# Integration: Semantic enrichment and API exposure
from ..company_ai.semantic_enrichment import generate_embeddings
from ..company_ai.api_integration import expose_api_endpoints

logger = logging.getLogger(__name__)

@retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(5))
def safe_get(session: requests.Session, url: str, timeout: int = 10) -> Optional[requests.Response]:
    """
    Perform a GET request with retry logic.
    """
    try:
        return session.get(url, timeout=timeout)
    except Exception as e:
        logger.error(f"[REQUEST ERROR] {url}: {e}")
        return None

def enrich_company(company_name: str, session: requests.Session, cache: dict, timeout: int = 10) -> Dict:
    """
    Enrich company with web scraping (placeholder for API integration).
    Returns a dictionary with company intelligence fields.
    """
    logger.info(f"[ENRICH] Researching: {company_name}")
    # Caching: skip if recently updated
    if company_name in cache:
        last_updated = cache[company_name].get('last_updated', '')
        try:
            if last_updated and (datetime.now() - datetime.fromisoformat(last_updated)).days < 30:
                logger.info(f"[CACHE] Using cached data for {company_name}")
                return cache[company_name]
        except Exception as e:
            logger.warning(f"[CACHE] Date parse failed for {company_name}: {e}")
    # Web enrichment
    try:
        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+official+website"
        response = safe_get(session, search_url, timeout)
        if not response or not response.ok:
            logger.warning(f"[WARN] Google search failed for {company_name}")
            return create_placeholder_company(company_name)
        soup = BeautifulSoup(response.content, 'html.parser')
        website_url = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/url?q=' in href and not any(skip in href.lower() for skip in ['google', 'youtube', 'facebook', 'linkedin']):
                website_url = href.split('/url?q=')[1].split('&')[0]
                break
        if not website_url:
            logger.warning(f"[WARN] Could not find website for {company_name}")
            return create_placeholder_company(company_name)
        company_data = extract_from_website(company_name, website_url, session, cache, timeout)
        # Integration: Semantic enrichment and API exposure
        embeddings = generate_embeddings(company_data)
        company_data['embeddings'] = embeddings
        logger.info(f"[ENRICHED] {company_name}: {website_url}")
        return company_data
    except Exception as e:
        logger.warning(f"[WARN] Search failed for {company_name}: {e}")
        return create_placeholder_company(company_name)

def extract_from_website(company_name: str, website_url: str, session: requests.Session, cache: dict, timeout: int = 10) -> Dict:
    """
    Extract company info from its website.
    """
    try:
        response = safe_get(session, website_url, timeout)
        if not response or not response.ok:
            logger.warning(f"[WARN] Website request failed for {company_name}")
            return create_placeholder_company(company_name)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')
        title_text = title.text.strip() if title else company_name
        description = ""
        meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        logo_url = extract_logo(soup, website_url)
        logo_path = None
        if logo_url:
            logo_path = download_logo(company_name, logo_url, session)
        industry = extract_industry_info(soup, company_name)
        company_data = {
            "name": company_name,
            "website": website_url,
            "title": title_text,
            "description": description[:500] if description else "Industry leader",
            "logo_url": logo_url,
            "logo_path": logo_path,
            "industry": industry,
            "last_updated": datetime.now().isoformat(),
            "status": "active",
            "intelligence_source": "web_scraper",
            "interactive_ready": True
        }
        cache[company_name] = company_data
        logger.info(f"[ENRICHED] {company_name}: {website_url}")
        return company_data
    except Exception as e:
        logger.warning(f"[WARN] Website extraction failed for {company_name}: {e}")
        return create_placeholder_company(company_name)

def extract_logo(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    logo_selectors = [
        'img[alt*="logo" i]',
        'img[src*="logo" i]',
        'img[class*="logo" i]',
        '.logo img',
        '#logo img',
        'header img',
        '.header img',
        '.navbar-brand img'
    ]
    for selector in logo_selectors:
        logos = soup.select(selector)
        for logo in logos:
            src = logo.get('src') or logo.get('data-src')
            if src:
                from urllib.parse import urljoin
                logo_url = urljoin(base_url, src)
                if is_valid_logo_url(logo_url):
                    return logo_url
    favicon = soup.find('link', {'rel': 'icon'}) or soup.find('link', {'rel': 'shortcut icon'})
    if favicon and favicon.get('href'):
        from urllib.parse import urljoin
        return urljoin(base_url, favicon['href'])
    return None

def is_valid_logo_url(url: str) -> bool:
    if not url:
        return False
    valid_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']
    if any(ext in url.lower() for ext in valid_extensions):
        return True
    logo_patterns = ['logo', 'brand', 'icon']
    return any(pattern in url.lower() for pattern in logo_patterns)

def download_logo(company_name: str, logo_url: str, session: requests.Session) -> Optional[str]:
    try:
        response = safe_get(session, logo_url, timeout=10)
        if response and response.status_code == 200:
            import re, os
            safe_name = re.sub(r'[^\w\s-]', '', company_name).strip()
            safe_name = re.sub(r'[-\s]+', '-', safe_name)
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'svg' in content_type:
                ext = '.svg'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.png'
            logo_path = os.path.join(LOGOS_DIR, f"{safe_name}{ext}")
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"[LOGO] Downloaded logo for {company_name}")
            return logo_path
    except Exception as e:
        logger.warning(f"[WARN] Logo download failed for {company_name}: {e}")
    return None

def extract_industry_info(soup: BeautifulSoup, company_name: str) -> str:
    text_content = soup.get_text().lower()
    industries = {
        'technology': ['software', 'tech', 'digital', 'ai', 'cloud', 'data'],
        'energy': ['oil', 'gas', 'renewable', 'solar', 'wind', 'energy', 'power'],
        'finance': ['bank', 'financial', 'investment', 'insurance', 'fintech'],
        'healthcare': ['health', 'medical', 'pharma', 'biotech', 'hospital'],
        'manufacturing': ['manufacturing', 'industrial', 'production', 'factory'],
        'consulting': ['consulting', 'advisory', 'services', 'strategy'],
        'engineering': ['engineering', 'construction', 'infrastructure']
    }
    for industry, keywords in industries.items():
        if any(keyword in text_content for keyword in keywords):
            return industry.title()
    return "Business Services"

def create_placeholder_company(company_name: str) -> Dict:
    return {
        "name": company_name,
        "website": f"https://www.google.com/search?q={company_name.replace(' ', '+')}",
        "title": company_name,
        "description": "Industry leader with global presence",
        "logo_url": None,
        "logo_path": None,
        "industry": "Business Services",
        "last_updated": datetime.now().isoformat(),
        "status": "placeholder",
        "intelligence_source": "placeholder",
        "interactive_ready": False
    }

# At module or app startup, call:
# expose_api_endpoints()
