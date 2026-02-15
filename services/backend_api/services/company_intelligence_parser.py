# --- Advanced web scraping integration ---
from advanced_web_scraper import robust_get
from bs4 import BeautifulSoup

# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntelliCV Company Intelligence Parser — Refactored (Robust + Safe)
- Safer search via DuckDuckGo HTML (no Google SERP scraping).
- Robots.txt awareness, retries/backoff, timeouts.
- Canonical domain keys + SQLite persistence, JSON export mirror.
- Deterministic logo extraction order.
- Weighted industry heuristic (easy to upgrade to ML later).
- Batch concurrency with domain locks + polite sleep.
"""

from __future__ import annotations
import argparse, contextlib, dataclasses, json, logging, os, re, sqlite3, threading, time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------- Paths ----------
PROJECT_ROOT = Path(__file__).resolve().parents[0]
AI_DATA_DIR = (PROJECT_ROOT / "ai_data").resolve()
COMPANY_DIR = AI_DATA_DIR / "companies"
DB_PATH = COMPANY_DIR / "market_intelligence.db"
JSON_EXPORT = COMPANY_DIR / "company_intelligence_database.json"
LOGO_DIR = COMPANY_DIR / "logos"
LOG_DIR = COMPANY_DIR / "logs"
for d in (AI_DATA_DIR, COMPANY_DIR, LOGO_DIR, LOG_DIR): d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "market_intelligence.log"
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()])
logger = logging.getLogger("company-intel")

# ---------- HTTP & Search ----------
USER_AGENT = "Mozilla/5.0 (compatible; IntelliCVBot/1.0; +https://example.com/bot)"
DEFAULT_TIMEOUT = 12
MAX_RETRIES = 3
BACKOFF = 0.6

DUCKDUCKGO_HTML = "https://duckduckgo.com/html/?q={q}"
DISALLOWED_HOSTS = {"facebook.com","youtube.com","linkedin.com","instagram.com","x.com","twitter.com"}

def mk_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=MAX_RETRIES, backoff_factor=BACKOFF,
                    status_forcelist=(429,500,502,503,504), allowed_methods=frozenset(["GET","HEAD"]),
                    raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=16)
    s.mount("http://", adapter); s.mount("https://", adapter)
    s.headers.update({"User-Agent": USER_AGENT})
    return s

def canonical_domain(url: str) -> Optional[str]:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host or None
    except: return None

def ddg_search_official_site(session: requests.Session, company: str) -> Optional[str]:
    url = DUCKDUCKGO_HTML.format(q=requests.utils.quote(f"{company} official site"))
    try:
        r = session.get(url, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__a, a.result__url"):
            href = a.get("href")
            if not href: continue
            host = urlparse(href).netloc.lower()
            if any(bad in host for bad in DISALLOWED_HOSTS): continue
            return href
    except Exception as e:
        logger.debug(f"DDG search error: {e}")
    return None

# ---------- Robots & polite fetching ----------
_robot_cache: Dict[str, robotparser.RobotFileParser] = {}
_domain_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)

def robots_allow(session: requests.Session, url: str) -> bool:
    netloc = urlparse(url).netloc
    if not netloc: return True
    rp = _robot_cache.get(netloc)
    if not rp:
        rp = robotparser.RobotFileParser()
        robots_url = f"{urlparse(url).scheme}://{netloc}/robots.txt"
        with contextlib.suppress(Exception):
            resp = session.get(robots_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
        _robot_cache[netloc] = rp
    return rp.can_fetch(USER_AGENT, url) if rp.default_entry is not None else True

def fetch_html(session: requests.Session, url: str) -> Optional[BeautifulSoup]:
    try:
        if not robots_allow(session, url): 
            logger.info(f"robots disallow: {url}"); return None
        r = session.get(url, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200 or not r.text: return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.debug(f"fetch error {url}: {e}"); return None

# ---------- Logo picking ----------
def is_logo_like(url: str) -> bool:
    u = url.lower()
    if any(ext in u for ext in (".png",".svg",".jpg",".jpeg",".webp",".gif",".ico","favicon")): return True
    return any(k in u for k in ("logo","brand"))

def guess_ext(url: str) -> str:
    u = url.lower()
    for ext in (".png",".svg",".jpg",".jpeg",".webp",".gif",".ico"):
        if ext in u: return ext
    return ".png"

def pick_logo(soup: BeautifulSoup, base_url: str) -> Tuple[Optional[str], Optional[str]]:
    if not soup: return None, None
    candidates = []
    for rel in ("apple-touch-icon","apple-touch-icon-precomposed","icon","shortcut icon","mask-icon"):
        for link in soup.find_all("link", rel=lambda v: v and rel in v):
            href = link.get("href");  candidates.append(href) if href else None
    og = soup.find("meta", {"property":"og:image"})
    if og and og.get("content"): candidates.append(og["content"])
    for sel in ['img[alt*="logo" i]','img[src*="logo" i]','img[class*="logo" i]','.logo img','#logo img','header img','.navbar-brand img']:
        for img in soup.select(sel):
            src = img.get("src") or img.get("data-src")
            candidates.append(src) if src else None
    for href in candidates:
        full = urljoin(base_url, href)
        if is_logo_like(full):
            return full, guess_ext(full)
    return None, None

# ---------- Industry heuristic ----------
INDUSTRY_KWS = {
    "Technology": ["software","platform","api","cloud","ai","data","saas","devops","ml"],
    "Finance": ["bank","lending","insurance","fintech","wealth","asset management","payments"],
    "Healthcare": ["clinical","medical","hospital","pharma","biotech","patient","diagnostic"],
    "Energy": ["renewable","solar","wind","oil","gas","power","utility"],
    "Manufacturing": ["manufacturing","industrial","factory","production","supply chain"],
    "Consulting": ["consulting","advisory","strategy","professional services"],
    "Retail": ["retail","ecommerce","store","omnichannel","consumer"],
}
def infer_industry(text: str) -> str:
    t = text.lower(); scores = defaultdict(int)
    for ind, kws in INDUSTRY_KWS.items():
        for kw in kws:
            if kw in t: scores[ind] += 1
    return max(scores.items(), key=lambda kv: kv[1])[0] if scores else "Business Services"

# ---------- Data model ----------
@dataclasses.dataclass
class CompanyRecord:
    name: str
    website: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    logo_path: Optional[str] = None
    industry: Optional[str] = None
    last_updated: str = dataclasses.field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"
    source: str = "web_enrichment"
    interactive_ready: bool = True
    domain: Optional[str] = None
    def asdict(self): return dataclasses.asdict(self)

# ---------- SQLite ----------
SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies(
    domain TEXT PRIMARY KEY,
    name TEXT, website TEXT, title TEXT, description TEXT,
    logo_url TEXT, logo_path TEXT, industry TEXT,
    last_updated TEXT, status TEXT, source TEXT, interactive_ready INTEGER
);
CREATE TABLE IF NOT EXISTS job_company_links(
    job_id TEXT,
    company_domain TEXT,
    job_title TEXT,
    job_description TEXT,
    link_source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(job_id, company_domain)
);
"""
def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;"); con.execute("PRAGMA synchronous=NORMAL;")
    return con
def db_init():
    with db() as con: con.executescript(SQL_SCHEMA)
def upsert(con: sqlite3.Connection, rec: CompanyRecord):
    con.execute("""
    INSERT INTO companies(domain,name,website,title,description,logo_url,logo_path,industry,last_updated,status,source,interactive_ready)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(domain) DO UPDATE SET
      name=excluded.name, website=excluded.website, title=excluded.title, description=excluded.description,
      logo_url=excluded.logo_url, logo_path=excluded.logo_path, industry=excluded.industry,
      last_updated=excluded.last_updated, status=excluded.status, source=excluded.source,
      interactive_ready=excluded.interactive_ready
    """, (rec.domain, rec.name, rec.website, rec.title, rec.description, rec.logo_url, rec.logo_path,
          rec.industry, rec.last_updated, rec.status, rec.source, 1 if rec.interactive_ready else 0))
def export_json():
    with db() as con:
        cur = con.execute("SELECT name,website,title,description,logo_url,logo_path,industry,last_updated,status,source,interactive_ready,domain FROM companies")
        rows = cur.fetchall()
    data = [{"name":r[0],"website":r[1],"title":r[2],"description":r[3],"logo_url":r[4],"logo_path":r[5],
             "industry":r[6],"last_updated":r[7],"status":r[8],"source":r[9],
             "interactive_ready":bool(r[10]),"domain":r[11]} for r in rows]
    JSON_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    JSON_EXPORT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- Core ----------
class CompanyIntel:

    def link_job_to_company(self, job_id: str, company_domain: str, job_title: str, job_description: str, link_source: str = "parser"):
        """
        Record a link between a job description and a company in the DB.
        """
        with db() as con:
            con.execute("""
                INSERT OR REPLACE INTO job_company_links (job_id, company_domain, job_title, job_description, link_source)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, company_domain, job_title, job_description, link_source))
            con.commit()

    def get_jobs_for_company(self, company_domain: str):
        """
        Retrieve all job descriptions linked to a company.
        """
        with db() as con:
            cur = con.execute("SELECT job_id, job_title, job_description, link_source, created_at FROM job_company_links WHERE company_domain=?", (company_domain,))
            return cur.fetchall()

    def get_companies_for_job(self, job_id: str):
        """
        Retrieve all companies linked to a job description.
        """
        with db() as con:
            cur = con.execute("SELECT company_domain, job_title, job_description, link_source, created_at FROM job_company_links WHERE job_id=?", (job_id,))
            return cur.fetchall()

    # TODO: Add user-facing analytics to probe company/job history for career pathing and aspiration matching
    def __init__(self, cache_days: int = 30, polite_sleep: float = 0.8):
        self.s = mk_session(); self.cache_days = cache_days; self.sleep = polite_sleep
        db_init()

    def _recent(self, iso: str) -> bool:
        try: return (datetime.utcnow() - datetime.fromisoformat(iso)) < timedelta(days=self.cache_days)
        except: return False

    def _download_logo(self, name: str, url: str, ext: str) -> Optional[str]:
        try:
            if not robots_allow(self.s, url): return None
            r = self.s.get(url, timeout=DEFAULT_TIMEOUT)
            if r.status_code != 200 or not r.content: return None
            fname = re.sub(r"[^\w\s-]","", name).strip()
            fname = re.sub(r"[-\s]+","-", fname) + ext
            path = LOGO_DIR / fname
            path.write_bytes(r.content)
            return str(path)
        except Exception as e:
            logger.debug(f"logo fail {url}: {e}"); return None

    def _cached_by_name(self, name: str) -> Optional[CompanyRecord]:
        with db() as con:
            row = con.execute("SELECT domain,name,website,title,description,logo_url,logo_path,industry,last_updated,status,source,interactive_ready FROM companies WHERE name=?", (name,)).fetchone()
        if not row: return None
        if row[8] and self._recent(row[8]):
            return CompanyRecord(name=row[1], website=row[2], title=row[3], description=row[4],
                                 logo_url=row[5], logo_path=row[6], industry=row[7], last_updated=row[8],
                                 status=row[9], source=row[10], interactive_ready=bool(row[11]), domain=row[0])
        return None

    def enrich(self, company: str, web_url: str = None) -> CompanyRecord:
        logger.info(f"[ENRICH] {company}")
        if (cached := self._cached_by_name(company)): return cached

        site = ddg_search_official_site(self.s, company)
        if not site:
            rec = CompanyRecord(name=company, website=f"https://duckduckgo.com/?q={requests.utils.quote(company)}",
                                description=None, industry=None,
                                status="unresolved", source="placeholder", interactive_ready=False, domain=None)
            with db() as con: upsert(con, rec); con.commit()
            return rec

        # --- Web scraping enrichment hook ---
        soup = None
        if web_url:
            resp = robust_get(web_url)
            if resp:
                soup = BeautifulSoup(resp.text, 'html.parser')
        if not soup:
            soup = fetch_html(self.s, site)

        title = (soup.title.get_text(strip=True) if soup and soup.title else company)
        desc = None
        if soup:
            m = soup.find("meta", {"name":"description"}) or soup.find("meta", {"property":"og:description"}) or soup.find("meta", {"name":"twitter:description"})
            if m and m.get("content"): desc = m["content"].strip()
        logo_url, logo_ext = pick_logo(soup, site)
        logo_path = None
        dom = canonical_domain(site)
        if logo_url and dom:
            lock = _domain_locks[dom]
            with lock: logo_path = self._download_logo(company, logo_url, logo_ext or ".png")
        text_for_ind = " ".join([title or "", desc or "", soup.get_text(" ", strip=True)[:1200] if soup else ""])
        industry = infer_industry(text_for_ind)

        rec = CompanyRecord(name=company, website=site, title=title[:300],
                            description=(desc[:600] if desc else None),
                            logo_url=logo_url, logo_path=logo_path, industry=industry,
                            status="active", source="web_enrichment", interactive_ready=True, domain=dom)
        with db() as con: upsert(con, rec); con.commit()
        time.sleep(self.sleep)
        return rec

    def enrich_many(self, companies: Iterable[str]) -> List[CompanyRecord]:
        results = []
        for c in companies:
            try: results.append(self.enrich(c))
            except Exception as e: logger.warning(f"enrich fail {c}: {e}")
        export_json()
        return results

    def extract_from_text(self, text: str) -> List[str]:
        suffix = r"(Ltd|Limited|Inc|Corporation|Corp\.?|Company|Co\.?|LLC|L\.L\.C\.|LLP|PLC|GmbH|AG|SA|Pvt|BV|NV|OY|AB|SpA|S\.A\.|SAS|KK|Pte|PTY)"
        pat = re.compile(rf"\b([A-Z][A-Za-z0-9&.,\- ]+\s{suffix})\b")
        seen, out = set(), []
        for m in pat.finditer(text):
            name = m.group(1).strip()
            if name not in seen: seen.add(name); out.append(name)
        return out

# Import enrichment logic
from market_intelligence.enrich import enrich_company

# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser(description="IntelliCV Company Intelligence (refactored)")
    p.add_argument("--companies", nargs="*", help="Company names to enrich")
    p.add_argument("--input-dir", type=str, help="Directory of .txt files to scan")
    p.add_argument("--cache-days", type=int, default=30)
    p.add_argument("--sleep", type=float, default=0.8)
    p.add_argument("--export-json", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    ci = CompanyIntel(cache_days=args.cache_days, polite_sleep=args.sleep)
    if args.input_dir:
        for fp in Path(args.input_dir).rglob("*.txt"):
            with contextlib.suppress(Exception):
                companies = ci.extract_from_text(fp.read_text(encoding="utf-8", errors="ignore"))
                if companies: ci.enrich_many(companies)
    if args.companies: ci.enrich_many(args.companies)
    if args.export_json: export_json()

def get_market_intelligence(company_name: str, session=None, cache=None, timeout=12):
    """
    Main entry point for company intelligence enrichment.
    """
    if session is None:
        session = mk_session()
    if cache is None:
        cache = {}
    # Call enrichment logic from enrich.py
    enriched = enrich_company(company_name, session, cache, timeout)
    return enriched

if __name__ == "__main__":
    main()
