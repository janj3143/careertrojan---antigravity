from __future__ import annotations
import requests
from shared.env import settings

class BackendClient:
    def __init__(self, base_url: str | None = None, timeout: int = 30):
        self.base_url = (base_url or settings.BACKEND_BASE_URL).rstrip("/")
        self.timeout = timeout

    def get(self, path: str, **params):
        url = f"{self.base_url}{path}"
        r = requests.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
