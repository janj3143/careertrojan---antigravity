import os
import httpx
from loguru import logger

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ID = os.getenv("GOOGLE_SEARCH_ID")

class CapabilityTester:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.search_id = GOOGLE_SEARCH_ID

    async def fetch_live_market_trends(self, queries):
        """
        Uses Google Custom Search API to fetch live data for capability validation.
        """
        if not self.api_key or not self.search_id:
            logger.warning("Google API credentials missing. Skipping live market test.")
            return []

        results = []
        async with httpx.AsyncClient() as client:
            for query in queries:
                try:
                    url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.search_id}&q={query}"
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    results.append(data.get("items", []))
                except Exception as e:
                    logger.error(f"Google API call failed for query '{query}': {e}")
        
        return results

# Global tester instance
capability_tester = CapabilityTester()
