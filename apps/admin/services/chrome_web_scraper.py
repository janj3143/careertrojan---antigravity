"""
Enhanced Chrome WebDriver-based web scraper for IntelliCV Admin Portal
Replaces Firefox with Chrome for better compatibility and performance
"""

import os
import time
import random
import requests
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromeWebScraper:
    """Enhanced Chrome WebDriver-based web scraper"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        
        # User agents for Chrome
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _setup_chrome_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with optimal options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Essential Chrome options for scraping
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            # Privacy and security options
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Performance optimization
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def robust_get(self, url: str, max_retries: int = 3, delay_range: tuple = (1, 3)) -> Optional[requests.Response]:
        """Robust HTTP GET with retry logic"""
        for attempt in range(max_retries):
            try:
                # Random delay to avoid rate limiting
                time.sleep(random.uniform(*delay_range))
                
                # Rotate user agent
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.info(f"Successfully fetched {url}")
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for {url}")
                    return None
                time.sleep(random.uniform(2, 5))
        
        return None
    
    def selenium_get(self, url: str, wait_time: int = 10) -> Optional[str]:
        """Use Selenium Chrome WebDriver for JavaScript-heavy sites"""
        if not self.driver:
            self.driver = self._setup_chrome_driver()
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            html_content = self.driver.page_source
            logger.info(f"Successfully scraped {url} with Selenium")
            return html_content
            
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Selenium scraping failed for {url}: {e}")
            return None
    
    def scrape_job_page(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """Scrape job page with fallback to Selenium if needed"""
        result = {"url": url, "scraping_method": "requests"}
        
        if use_selenium:
            html_content = self.selenium_get(url)
            result["scraping_method"] = "selenium"
        else:
            response = self.robust_get(url)
            html_content = response.text if response else None
        
        if not html_content:
            return {**result, "error": "Failed to fetch page content"}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Enhanced job page parsing
            title = self._extract_job_title(soup)
            company = self._extract_company_name(soup)
            location = self._extract_location(soup)
            description = self._extract_job_description(soup)
            requirements = self._extract_requirements(soup)
            salary = self._extract_salary_info(soup)
            
            return {
                **result,
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "requirements": requirements,
                "salary": salary,
                "scraped_successfully": True
            }
            
        except Exception as e:
            logger.error(f"Failed to parse job page {url}: {e}")
            return {**result, "error": f"Parsing failed: {e}"}
    
    def _extract_job_title(self, soup: BeautifulSoup) -> str:
        """Extract job title using multiple selectors"""
        selectors = [
            'h1[data-testid="job-title"]',
            'h1.job-title',
            'h1[class*="title"]',
            '.job-header h1',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """Extract company name using multiple selectors"""
        selectors = [
            '[data-testid="company-name"]',
            '.company-name',
            '[class*="company"]',
            '.employer-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract job location"""
        selectors = [
            '[data-testid="job-location"]',
            '.job-location',
            '[class*="location"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def _extract_job_description(self, soup: BeautifulSoup) -> str:
        """Extract job description"""
        selectors = [
            '[data-testid="job-description"]',
            '.job-description',
            '.job-summary',
            '[class*="description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements sections
        req_sections = soup.select('.requirements li, .qualifications li, ul[class*="requirement"] li')
        for li in req_sections:
            req_text = li.get_text(strip=True)
            if req_text and len(req_text) > 10:
                requirements.append(req_text)
        
        return requirements
    
    def _extract_salary_info(self, soup: BeautifulSoup) -> str:
        """Extract salary information"""
        selectors = [
            '[data-testid="salary"]',
            '.salary',
            '[class*="salary"]',
            '[class*="compensation"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def batch_scrape_jobs(self, urls: List[str], use_selenium: bool = False, 
                         delay_range: tuple = (2, 5)) -> List[Dict[str, Any]]:
        """Batch scrape multiple job URLs"""
        results = []
        
        logger.info(f"Starting batch scrape of {len(urls)} URLs")
        
        for i, url in enumerate(urls):
            logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
            
            result = self.scrape_job_page(url, use_selenium=use_selenium)
            results.append(result)
            
            # Random delay between requests
            if i < len(urls) - 1:
                delay = random.uniform(*delay_range)
                time.sleep(delay)
        
        return results
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions for backward compatibility
def robust_get(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Backward compatible robust GET function"""
    scraper = ChromeWebScraper(headless=True)
    try:
        return scraper.robust_get(url, max_retries)
    finally:
        scraper.close()

def scrape_job_page(url: str, use_selenium: bool = False) -> Dict[str, Any]:
    """Backward compatible job scraping function"""
    scraper = ChromeWebScraper(headless=True)
    try:
        return scraper.scrape_job_page(url, use_selenium)
    finally:
        scraper.close()


if __name__ == "__main__":
    # Test the Chrome web scraper
    test_urls = [
        "https://www.example.com/job/1",
        "https://www.example.com/job/2"
    ]
    
    with ChromeWebScraper(headless=True) as scraper:
        results = scraper.batch_scrape_jobs(test_urls)
        
        for result in results:
            print(f"URL: {result['url']}")
            print(f"Method: {result.get('scraping_method', 'unknown')}")
            print(f"Success: {result.get('scraped_successfully', False)}")
            print("---")