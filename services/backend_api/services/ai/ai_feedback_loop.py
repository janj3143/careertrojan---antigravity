"""
=============================================================================
IntelliCV AI Feedback Loop System - Intelligent Research & Learning
=============================================================================

Advanced feedback loop system for unknown data flagging and automated research:

🔍 UNKNOWN DATA DETECTION:
- Flag terms not in learning table with confidence < threshold
- Identify inconsistent or ambiguous extractions
- Queue low-confidence entities for batch research
- Detect patterns in failed parsing attempts

🌐 WEB RESEARCH INTEGRATION:
- Automated Google/Bing searches for unknown terms
- LinkedIn and industry site scraping for job titles
- Company database lookups for validation
- Wikipedia and domain-specific knowledge extraction

💬 CHAT AI RESEARCH:
- OpenAI/Claude queries for term definitions
- Industry-specific context understanding
- Confidence scoring for AI responses
- Multi-source validation and consensus

🧠 LEARNING INTEGRATION:
- Update learning table with research findings
- Adjust thresholds based on accuracy feedback
- Retrain models with verified data
- Continuous improvement through feedback cycles

🔄 BATCH PROCESSING:
- Queue management with priority scoring
- Scheduled research runs (daily/weekly)
- Rate limiting for API calls
- Results validation and quality scoring

Author: IntelliCV AI Integration Team
Purpose: Production-ready feedback loop with real research capabilities
Environment: IntelliCV\env310 with web scraping and AI integration
"""

import json
import requests
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
from urllib.parse import quote_plus
import re

# Web scraping imports
try:
    from bs4 import BeautifulSoup
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

# AI/Chat integration imports
try:
    import openai
    from transformers import pipeline
    AI_CHAT_AVAILABLE = True
except ImportError:
    AI_CHAT_AVAILABLE = False

# =============================================================================
# RESEARCH CONFIGURATION
# =============================================================================

@dataclass
class ResearchConfig:
    """Configuration for feedback loop research system"""

    # API Keys and credentials
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    bing_api_key: Optional[str] = None

    # Research preferences
    max_web_results: int = 5
    max_ai_queries: int = 3
    research_timeout_seconds: int = 30

    # Rate limiting
    requests_per_minute: int = 60
    daily_research_limit: int = 1000
    api_call_delay: float = 1.0

    # Quality thresholds
    min_confidence_score: float = 0.7
    consensus_threshold: int = 2  # Sources needed for consensus
    max_research_attempts: int = 3

    # Research sources
    enable_web_search: bool = True
    enable_linkedin_research: bool = False  # Requires special setup
    enable_wikipedia: bool = True
    enable_ai_chat: bool = True
    enable_company_db: bool = True

    # Batch processing
    batch_size: int = 10
    processing_interval_hours: int = 6
    priority_processing: bool = True

# =============================================================================
# RESEARCH RESULT CLASSES
# =============================================================================

@dataclass
class ResearchResult:
    """Single research result from a source"""
    source: str
    term: str
    definition: str
    confidence: float
    context: str
    url: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConsolidatedResearch:
    """Consolidated research results from multiple sources"""
    term: str
    category: str
    best_definition: str
    confidence: float
    sources: List[ResearchResult]
    consensus_count: int
    research_timestamp: datetime
    should_learn: bool
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            'term': self.term,
            'category': self.category,
            'best_definition': self.best_definition,
            'confidence': self.confidence,
            'sources': [asdict(source) for source in self.sources],
            'consensus_count': self.consensus_count,
            'research_timestamp': self.research_timestamp.isoformat(),
            'should_learn': self.should_learn,
            'metadata': self.metadata or {}
        }

# =============================================================================
# WEB RESEARCH ENGINE
# =============================================================================

class WebResearchEngine:
    """
    Web research engine for automated term research using multiple sources.
    Handles rate limiting, caching, and result validation.
    """

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IntelliCV-Research/1.0 (Educational Purpose)'
        })

        # Rate limiting
        self.last_request_time = 0
        self.daily_requests = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Results cache
        self.cache = {}
        self.cache_ttl = timedelta(hours=24)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = time.time()

        # Reset daily counter if needed
        if datetime.now() >= self.daily_reset_time + timedelta(days=1):
            self.daily_requests = 0
            self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check daily limit
        if self.daily_requests >= self.config.daily_research_limit:
            raise Exception("Daily research limit exceeded")

        # Check per-minute rate limiting
        time_since_last = now - self.last_request_time
        if time_since_last < (60 / self.config.requests_per_minute):
            sleep_time = (60 / self.config.requests_per_minute) - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.daily_requests += 1

    def _check_cache(self, term: str, category: str) -> Optional[List[ResearchResult]]:
        """Check if research results are cached"""
        cache_key = f"{term}:{category}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                self.logger.info(f"Using cached results for {term}")
                return cached_data
            else:
                # Cache expired
                del self.cache[cache_key]

        return None

    def _cache_results(self, term: str, category: str, results: List[ResearchResult]):
        """Cache research results"""
        cache_key = f"{term}:{category}"
        self.cache[cache_key] = (results, datetime.now())

    def research_term(self, term: str, category: str, context: str = "") -> List[ResearchResult]:
        """
        Research a term using multiple web sources.

        Args:
            term: Term to research
            category: Category of term (job_title, skill, company, etc.)
            context: Additional context for research

        Returns:
            List of research results from different sources
        """
        # Check cache first
        cached_results = self._check_cache(term, category)
        if cached_results:
            return cached_results

        results = []

        try:
            # Wikipedia research
            if self.config.enable_wikipedia:
                wiki_result = self._research_wikipedia(term, category, context)
                if wiki_result:
                    results.append(wiki_result)

            # Google search research
            if self.config.enable_web_search and self.config.google_api_key:
                google_results = self._research_google(term, category, context)
                results.extend(google_results)

            # Web scrape search (doesn't require API; still live web data)
            elif self.config.enable_web_search:
                web_results = self._research_web_scrape(term, category, context)
                results.extend(web_results)

            # Company database lookup
            if self.config.enable_company_db and category == 'companies':
                company_result = self._research_company_db(term, context)
                if company_result:
                    results.append(company_result)

            # Cache results
            self._cache_results(term, category, results)

            self.logger.info(f"Researched {term}: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Web research failed for {term}: {e}")
            return results

    def _research_wikipedia(self, term: str, category: str, context: str) -> Optional[ResearchResult]:
        """Research term on Wikipedia"""
        try:
            self._rate_limit_check()

            # Wikipedia API search
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(term)

            response = self.session.get(search_url, timeout=self.config.research_timeout_seconds)

            if response.status_code == 200:
                data = response.json()

                if 'extract' in data and data['extract']:
                    # Calculate confidence based on term presence and extract quality
                    extract = data['extract']
                    confidence = 0.8  # Wikipedia is generally reliable

                    # Boost confidence if term appears in extract
                    if term.lower() in extract.lower():
                        confidence += 0.1

                    # Reduce confidence for disambiguation pages
                    if 'disambiguation' in extract.lower():
                        confidence -= 0.3

                    return ResearchResult(
                        source="wikipedia",
                        term=term,
                        definition=extract[:500] + "..." if len(extract) > 500 else extract,
                        confidence=max(0.1, min(1.0, confidence)),
                        context=f"Wikipedia article for {term}",
                        url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        metadata={'full_extract': extract, 'wikipedia_id': data.get('pageid')}
                    )

        except Exception as e:
            self.logger.error(f"Wikipedia research failed for {term}: {e}")

        return None

    def _research_google(self, term: str, category: str, context: str) -> List[ResearchResult]:
        """Research term using Google Custom Search API"""
        results = []

        if not self.config.google_api_key:
            return results

        try:
            self._rate_limit_check()

            # Construct search query based on category
            search_queries = self._build_search_queries(term, category, context)

            for query in search_queries[:2]:  # Limit to 2 queries to save API calls
                search_url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.config.google_api_key,
                    'cx': '017576662512468239146:omuauf_lfve',  # Example CSE ID
                    'q': query,
                    'num': min(3, self.config.max_web_results)
                }

                response = self.session.get(search_url, params=params,
                                          timeout=self.config.research_timeout_seconds)

                if response.status_code == 200:
                    data = response.json()

                    for item in data.get('items', [])[:self.config.max_web_results]:
                        # Extract snippet and calculate confidence
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')

                        confidence = self._calculate_web_confidence(term, title, snippet, category)

                        if confidence >= self.config.min_confidence_score:
                            results.append(ResearchResult(
                                source="google_search",
                                term=term,
                                definition=snippet,
                                confidence=confidence,
                                context=f"Google search: {query}",
                                url=item.get('link', ''),
                                metadata={
                                    'title': title,
                                    'search_query': query,
                                    'display_link': item.get('displayLink', '')
                                }
                            ))

                # Small delay between API calls
                time.sleep(self.config.api_call_delay)

        except Exception as e:
            self.logger.error(f"Google search failed for {term}: {e}")

        return results

    def _research_web_scrape(self, term: str, category: str, context: str) -> List[ResearchResult]:
        """Web research without API (basic scraping). Returns only live web snippets."""
        results = []

        if not SCRAPING_AVAILABLE:
            return results

        try:
            self._rate_limit_check()

            # Simple DuckDuckGo search (doesn't require API)
            search_query = self._build_search_queries(term, category, context)[0]
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"

            response = self.session.get(search_url, timeout=self.config.research_timeout_seconds)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract search results
                result_elements = soup.find_all('div', class_='result')[:self.config.max_web_results]

                for element in result_elements:
                    try:
                        title_elem = element.find('a', class_='result__a')
                        snippet_elem = element.find('a', class_='result__snippet')

                        if title_elem and snippet_elem:
                            title = title_elem.get_text(strip=True)
                            snippet = snippet_elem.get_text(strip=True)
                            url = title_elem.get('href', '')

                            confidence = self._calculate_web_confidence(term, title, snippet, category)

                            if confidence >= self.config.min_confidence_score:
                                results.append(ResearchResult(
                                    source="web_search",
                                    term=term,
                                    definition=snippet[:300],
                                    confidence=confidence,
                                    context=f"Web search: {search_query}",
                                    url=url,
                                    metadata={'title': title, 'search_engine': 'duckduckgo'}
                                ))

                    except Exception as e:
                        self.logger.warning(f"Failed to parse search result: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Web fallback research failed for {term}: {e}")

        return results

    def _research_company_db(self, term: str, context: str) -> Optional[ResearchResult]:
        """Research company in database/APIs"""
        try:
            # No demo/mock data allowed. Only return results sourced from live APIs
            # or real databases wired into the system.
            return None

        except Exception as e:
            self.logger.error(f"Company database research failed for {term}: {e}")

        return None

    def _build_search_queries(self, term: str, category: str, context: str) -> List[str]:
        """Build search queries based on term category"""
        base_queries = [f'"{term}" definition']

        if category == 'job_titles':
            base_queries.extend([
                f'"{term}" job role responsibilities',
                f'"{term}" career position description',
                f'what is {term} job'
            ])
        elif category == 'skills':
            base_queries.extend([
                f'"{term}" technology skill',
                f'"{term}" programming language',
                f'learn {term} tutorial'
            ])
        elif category == 'companies':
            base_queries.extend([
                f'"{term}" company about',
                f'"{term}" corporation business',
                f'"{term}" company profile'
            ])
        elif category == 'terminology':
            base_queries.extend([
                f'"{term}" technical term',
                f'"{term}" industry terminology',
                f'"{term}" professional definition'
            ])

        return base_queries[:3]  # Limit to top 3 queries

    def _calculate_web_confidence(self, term: str, title: str, snippet: str, category: str) -> float:
        """Calculate confidence score for web search result"""
        confidence = 0.5  # Base confidence

        # Term presence in title (high weight)
        if term.lower() in title.lower():
            confidence += 0.3

        # Term presence in snippet
        if term.lower() in snippet.lower():
            confidence += 0.2

        # Category-specific keywords
        category_keywords = {
            'job_titles': ['job', 'role', 'position', 'career', 'responsibilities', 'duties'],
            'skills': ['skill', 'technology', 'programming', 'software', 'tool', 'framework'],
            'companies': ['company', 'corporation', 'business', 'organization', 'firm'],
            'terminology': ['definition', 'meaning', 'term', 'glossary', 'concept']
        }

        keywords = category_keywords.get(category, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in snippet.lower())
        confidence += (keyword_matches / len(keywords)) * 0.3

        # Penalize very short snippets
        if len(snippet) < 50:
            confidence -= 0.2

        # Penalize results with too many unrelated words
        unrelated_words = ['error', '404', 'not found', 'unavailable', 'missing']
        if any(word in snippet.lower() for word in unrelated_words):
            confidence -= 0.4

        return max(0.1, min(1.0, confidence))

# =============================================================================
# AI CHAT RESEARCH ENGINE
# =============================================================================

class AIChatResearchEngine:
    """
    AI chat research engine using OpenAI, Claude, or local models
    for term definition and context understanding.
    """

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.openai_client = None
        self.local_models = {}

        # Initialize OpenAI if available
        if self.config.openai_api_key and AI_CHAT_AVAILABLE:
            try:
                openai.api_key = self.config.openai_api_key
                self.openai_client = openai
                self.logger = logging.getLogger(__name__)
                self.logger.info("OpenAI client initialized for research")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI: {e}")

        # Local/heuristic model fallbacks are intentionally disabled to avoid
        # producing non-sourced definitions.

    def _load_local_models(self):
        """Load local transformer models for AI research"""
        try:
            # Load Q&A model for definitions
            self.local_models['qa'] = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=-1  # CPU
            )

            self.logger.info("Local AI models loaded for research")

        except Exception as e:
            self.logger.error(f"Failed to load local AI models: {e}")

    def research_with_ai(self, term: str, category: str, context: str = "") -> List[ResearchResult]:
        """
        Research term using AI chat models.

        Args:
            term: Term to research
            category: Category of term
            context: Additional context

        Returns:
            List of AI research results
        """
        results = []

        try:
            # OpenAI research (only when explicitly configured).
            if self.openai_client:
                openai_result = self._research_openai(term, category, context)
                if openai_result:
                    results.append(openai_result)
            else:
                # No fabricated or pattern-based definitions permitted.
                self.logger.warning(
                    "AI research is unavailable (no OpenAI client configured); returning no results."
                )

            return results

        except Exception as e:
            self.logger.error(f"AI research failed for {term}: {e}")
            return results

    def _research_openai(self, term: str, category: str, context: str) -> Optional[ResearchResult]:
        """Research using OpenAI ChatGPT"""
        try:
            # Build category-specific prompt
            prompt = self._build_ai_prompt(term, category, context)

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional industry expert providing accurate, concise definitions for CV/resume terminology. Focus on practical, workplace-relevant information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3,  # Lower temperature for more factual responses
                timeout=self.config.research_timeout_seconds
            )

            definition = response.choices[0].message.content.strip()

            # Calculate confidence based on response quality
            confidence = self._calculate_ai_confidence(term, definition, category)

            if confidence >= self.config.min_confidence_score:
                return ResearchResult(
                    source="openai_gpt",
                    term=term,
                    definition=definition,
                    confidence=confidence,
                    context=f"AI research for {category}: {term}",
                    metadata={
                        'model': 'gpt-3.5-turbo',
                        'tokens_used': response.usage.total_tokens,
                        'prompt': prompt[:100] + "..."
                    }
                )

        except Exception as e:
            self.logger.error(f"OpenAI research failed for {term}: {e}")

        return None

    def _research_local_model(self, term: str, category: str, context: str) -> Optional[ResearchResult]:
        raise RuntimeError("Local model research is disabled (no non-sourced definitions).")

    def _research_fallback(self, term: str, category: str, context: str) -> Optional[ResearchResult]:
        raise RuntimeError("Fallback pattern research is disabled (no fabricated definitions).")

    def _build_ai_prompt(self, term: str, category: str, context: str) -> str:
        """Build AI prompt based on term category"""
        base_prompt = f'Define "{term}" in a professional context.'

        if category == 'job_titles':
            return f'Define the job title "{term}". Include typical responsibilities, required skills, and industry context. Be concise and professional.'

        elif category == 'skills':
            return f'Define the professional skill or technology "{term}". Include what it is, how it\'s used in the workplace, and its importance. Be concise.'

        elif category == 'companies':
            return f'Provide a brief overview of the company "{term}". Include industry, main business, and general information. Be factual and concise.'

        elif category == 'terminology':
            return f'Define the professional term "{term}". Explain its meaning in business or industry context. Be clear and concise.'

        else:
            return f'Define "{term}" in a professional context. Provide a clear, concise definition suitable for resume/CV analysis.'

    def _calculate_ai_confidence(self, term: str, definition: str, category: str) -> float:
        """Calculate confidence score for AI-generated definition"""
        confidence = 0.7  # Base confidence for AI responses

        # Check if term appears in definition
        if term.lower() in definition.lower():
            confidence += 0.1

        # Check definition length (not too short, not too long)
        def_length = len(definition)
        if 50 <= def_length <= 300:
            confidence += 0.1
        elif def_length < 20 or def_length > 500:
            confidence -= 0.2

        # Check for category-relevant keywords
        category_keywords = {
            'job_titles': ['role', 'position', 'responsibilities', 'job', 'career', 'professional'],
            'skills': ['skill', 'technology', 'competency', 'expertise', 'ability', 'proficiency'],
            'companies': ['company', 'business', 'organization', 'corporation', 'firm', 'enterprise'],
            'terminology': ['term', 'concept', 'definition', 'meaning', 'refers to', 'professional']
        }

        keywords = category_keywords.get(category, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in definition.lower())
        confidence += (keyword_matches / len(keywords)) * 0.2

        # Penalize vague or generic responses
        vague_indicators = ['various', 'many things', 'depends on', 'can be', 'might be', 'unclear']
        if any(indicator in definition.lower() for indicator in vague_indicators):
            confidence -= 0.3

        return max(0.1, min(1.0, confidence))

# =============================================================================
# FEEDBACK LOOP ORCHESTRATOR
# =============================================================================

class AIFeedbackLoopSystem:
    """
    Main orchestrator for the AI feedback loop system.
    Manages research queue, coordinates web and AI research,
    consolidates results, and updates learning systems.
    """

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.web_engine = WebResearchEngine(config)
        self.ai_engine = AIChatResearchEngine(config)

        # Research queue and results storage
        self.research_queue = []
        self.completed_research = {}
        self.failed_research = {}

        # Statistics
        self.stats = {
            'total_researched': 0,
            'successful_research': 0,
            'failed_research': 0,
            'terms_learned': 0,
            'avg_confidence': 0.0,
            'research_sources_used': defaultdict(int)
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.logger.info("AI Feedback Loop System initialized")

    def flag_unknown_term(self, term: str, category: str, context: str = "",
                         priority: int = 1) -> bool:
        """
        Flag an unknown term for research.

        Args:
            term: Unknown term to research
            category: Category of term (job_title, skill, etc.)
            context: Context where term was found
            priority: Research priority (1=low, 5=high)

        Returns:
            Success status
        """
        try:
            # Check if already in queue or completed
            queue_key = f"{term}:{category}"

            if queue_key in [f"{item['term']}:{item['category']}" for item in self.research_queue]:
                self.logger.info(f"Term already in research queue: {term}")
                return True

            if queue_key in self.completed_research:
                self.logger.info(f"Term already researched: {term}")
                return True

            # Add to research queue
            research_item = {
                'term': term,
                'category': category,
                'context': context,
                'priority': priority,
                'flagged_time': datetime.now(),
                'attempts': 0,
                'status': 'queued'
            }

            # Insert based on priority (higher priority first)
            inserted = False
            for i, item in enumerate(self.research_queue):
                if priority > item['priority']:
                    self.research_queue.insert(i, research_item)
                    inserted = True
                    break

            if not inserted:
                self.research_queue.append(research_item)

            self.logger.info(f"Flagged unknown term for research: {term} (category: {category}, priority: {priority})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to flag unknown term {term}: {e}")
            return False

    def process_research_batch(self, batch_size: int = None) -> Dict[str, Any]:
        """
        Process a batch of research items from the queue.

        Args:
            batch_size: Number of items to process (uses config default if None)

        Returns:
            Batch processing results
        """
        if batch_size is None:
            batch_size = self.config.batch_size

        batch_results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'learned': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            # Get items to process
            items_to_process = self.research_queue[:batch_size]

            if not items_to_process:
                self.logger.info("No items in research queue")
                return batch_results

            self.logger.info(f"Processing research batch: {len(items_to_process)} items")

            for item in items_to_process:
                try:
                    # Remove from queue
                    self.research_queue.remove(item)
                    item['status'] = 'processing'
                    item['attempts'] += 1

                    # Skip if too many attempts
                    if item['attempts'] > self.config.max_research_attempts:
                        batch_results['skipped'] += 1
                        self.failed_research[f"{item['term']}:{item['category']}"] = {
                            'item': item,
                            'reason': 'max_attempts_exceeded',
                            'timestamp': datetime.now()
                        }
                        continue

                    # Research the term
                    consolidated_result = self.research_term_comprehensive(
                        item['term'],
                        item['category'],
                        item['context']
                    )

                    batch_results['processed'] += 1

                    if consolidated_result and consolidated_result.confidence >= self.config.min_confidence_score:
                        # Successful research
                        batch_results['successful'] += 1

                        # Store result
                        result_key = f"{item['term']}:{item['category']}"
                        self.completed_research[result_key] = consolidated_result

                        # Check if should learn
                        if consolidated_result.should_learn:
                            batch_results['learned'] += 1
                            self.stats['terms_learned'] += 1

                        # Update statistics
                        self.stats['successful_research'] += 1
                        self.stats['avg_confidence'] = (
                            (self.stats['avg_confidence'] * (self.stats['successful_research'] - 1)) +
                            consolidated_result.confidence
                        ) / self.stats['successful_research']

                        for source in consolidated_result.sources:
                            self.stats['research_sources_used'][source.source] += 1

                        item['status'] = 'completed'
                        self.logger.info(f"Successfully researched: {item['term']} (confidence: {consolidated_result.confidence:.2f})")

                    else:
                        # Failed research
                        batch_results['failed'] += 1
                        self.stats['failed_research'] += 1

                        # Put back in queue with lower priority if not max attempts
                        if item['attempts'] < self.config.max_research_attempts:
                            item['status'] = 'queued'
                            item['priority'] = max(1, item['priority'] - 1)  # Lower priority
                            self.research_queue.append(item)
                        else:
                            self.failed_research[f"{item['term']}:{item['category']}"] = {
                                'item': item,
                                'reason': 'low_confidence',
                                'timestamp': datetime.now(),
                                'result': consolidated_result
                            }

                        self.logger.warning(f"Research failed for: {item['term']} (low confidence)")

                    self.stats['total_researched'] += 1

                    # Rate limiting delay
                    time.sleep(self.config.api_call_delay)

                except Exception as e:
                    batch_results['errors'].append(f"Error processing {item['term']}: {str(e)}")
                    self.logger.error(f"Error processing research item {item['term']}: {e}")

                    # Put item back in queue
                    item['status'] = 'queued'
                    if item['attempts'] < self.config.max_research_attempts:
                        self.research_queue.append(item)

            self.logger.info(f"Batch processing completed: {batch_results}")
            return batch_results

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            batch_results['errors'].append(f"Batch processing error: {str(e)}")
            return batch_results

    def research_term_comprehensive(self, term: str, category: str, context: str = "") -> Optional[ConsolidatedResearch]:
        """
        Comprehensive research of a term using multiple sources.

        Args:
            term: Term to research
            category: Category of term
            context: Additional context

        Returns:
            Consolidated research results
        """
        try:
            all_results = []

            # Web research
            if self.config.enable_web_search:
                web_results = self.web_engine.research_term(term, category, context)
                all_results.extend(web_results)
                self.logger.debug(f"Web research for {term}: {len(web_results)} results")

            # AI chat research
            if self.config.enable_ai_chat:
                ai_results = self.ai_engine.research_with_ai(term, category, context)
                all_results.extend(ai_results)
                self.logger.debug(f"AI research for {term}: {len(ai_results)} results")

            if not all_results:
                self.logger.warning(f"No research results found for {term}")
                return None

            # Consolidate results
            consolidated = self._consolidate_research_results(term, category, all_results)

            self.logger.info(f"Comprehensive research completed for {term}: confidence {consolidated.confidence:.2f}")
            return consolidated

        except Exception as e:
            self.logger.error(f"Comprehensive research failed for {term}: {e}")
            return None

    def _consolidate_research_results(self, term: str, category: str,
                                    results: List[ResearchResult]) -> ConsolidatedResearch:
        """Consolidate multiple research results into a single result"""
        if not results:
            return None

        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)

        # Find consensus definition (most common theme)
        definitions = [r.definition for r in results]
        best_definition = definitions[0]  # Start with highest confidence

        # Calculate overall confidence (weighted average)
        total_weight = sum(r.confidence for r in results)
        weighted_confidence = sum(r.confidence * r.confidence for r in results) / max(total_weight, 1)

        # Count sources that agree (simplified consensus)
        consensus_count = len(set(r.source for r in results))

        # Determine if should learn (high confidence and consensus)
        should_learn = (
            weighted_confidence >= self.config.min_confidence_score and
            consensus_count >= self.config.consensus_threshold
        )

        # Create consolidated result
        consolidated = ConsolidatedResearch(
            term=term,
            category=category,
            best_definition=best_definition,
            confidence=weighted_confidence,
            sources=results,
            consensus_count=consensus_count,
            research_timestamp=datetime.now(),
            should_learn=should_learn,
            metadata={
                'source_types': [r.source for r in results],
                'confidence_range': [min(r.confidence for r in results), max(r.confidence for r in results)],
                'definition_lengths': [len(r.definition) for r in results]
            }
        )

        return consolidated

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive feedback loop system status"""
        return {
            'research_queue': {
                'total_items': len(self.research_queue),
                'by_priority': dict(Counter(item['priority'] for item in self.research_queue)),
                'by_category': dict(Counter(item['category'] for item in self.research_queue)),
                'oldest_item': min([item['flagged_time'] for item in self.research_queue], default=None),
                'newest_item': max([item['flagged_time'] for item in self.research_queue], default=None)
            },
            'completed_research': {
                'total_completed': len(self.completed_research),
                'by_category': dict(Counter(r.category for r in self.completed_research.values())),
                'avg_confidence': sum(r.confidence for r in self.completed_research.values()) / max(len(self.completed_research), 1),
                'learned_terms': sum(1 for r in self.completed_research.values() if r.should_learn)
            },
            'failed_research': {
                'total_failed': len(self.failed_research),
                'failure_reasons': dict(Counter(f['reason'] for f in self.failed_research.values()))
            },
            'statistics': self.stats,
            'configuration': {
                'min_confidence_score': self.config.min_confidence_score,
                'consensus_threshold': self.config.consensus_threshold,
                'max_research_attempts': self.config.max_research_attempts,
                'batch_size': self.config.batch_size,
                'research_sources_enabled': {
                    'web_search': self.config.enable_web_search,
                    'ai_chat': self.config.enable_ai_chat,
                    'wikipedia': self.config.enable_wikipedia,
                    'company_db': self.config.enable_company_db
                }
            }
        }

    def export_research_data(self, export_path: str) -> bool:
        """Export all research data for backup or analysis"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'research_queue': self.research_queue,
                'completed_research': {k: v.to_dict() for k, v in self.completed_research.items()},
                'failed_research': self.failed_research,
                'configuration': {
                    'min_confidence_score': self.config.min_confidence_score,
                    'consensus_threshold': self.config.consensus_threshold,
                    'max_research_attempts': self.config.max_research_attempts,
                    'batch_size': self.config.batch_size,
                    'daily_research_limit': self.config.daily_research_limit
                }
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Research data exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export research data: {e}")
            return False

# =============================================================================
# MAIN EXECUTION & TESTING
# =============================================================================

if __name__ == "__main__":
    # Example usage and testing
    print("IntelliCV AI Feedback Loop System - Testing")

    # Initialize configuration
    config = ResearchConfig(
        openai_api_key=None,  # Add your API key for full functionality
        google_api_key=None,  # Add your Google API key
        max_web_results=3,
        min_confidence_score=0.6,
        consensus_threshold=2,
        batch_size=5,
        enable_web_search=True,
        enable_wikipedia=True,
        enable_ai_chat=True
    )

    # Initialize feedback loop system
    feedback_system = AIFeedbackLoopSystem(config)

    # Test flagging unknown terms
    print("\nTesting unknown term flagging...")
    test_terms = [
        ("DevOps Engineer", "job_titles", "Found in CV header", 3),
        ("TensorFlow", "skills", "Listed under technical skills", 2),
        ("Kubernetes", "skills", "Mentioned in job description", 2),
        ("Acme Corp", "companies", "Previous employer", 1),
        ("CI/CD", "terminology", "Technical abbreviation", 3)
    ]

    for term, category, context, priority in test_terms:
        success = feedback_system.flag_unknown_term(term, category, context, priority)
        print(f"Flagged {term}: {'Success' if success else 'Failed'}")

    # Test batch processing
    print("\nTesting batch processing...")
    batch_results = feedback_system.process_research_batch(batch_size=3)
    print(f"Batch results: {batch_results}")

    # Show completed research
    print("\nCompleted research:")
    for key, result in feedback_system.completed_research.items():
        print(f"  {key}: {result.best_definition[:100]}... (confidence: {result.confidence:.2f})")

    # Get system status
    print("\nSystem Status:")
    status = feedback_system.get_system_status()
    print(f"Queue items: {status['research_queue']['total_items']}")
    print(f"Completed research: {status['completed_research']['total_completed']}")
    print(f"Average confidence: {status['completed_research']['avg_confidence']:.2f}")
    print(f"Terms learned: {status['completed_research']['learned_terms']}")

    # Export research data
    export_file = "feedback_loop_export.json"
    success = feedback_system.export_research_data(export_file)
    print(f"Export to {export_file}: {'Success' if success else 'Failed'}")

    print("\nAI Feedback Loop System testing completed!")
