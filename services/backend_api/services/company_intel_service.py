from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.shared.paths import CareerTrojanPaths

try:
    from services.backend_api.services.company_intelligence.extract import extract_companies
except Exception:
    extract_companies = None


@dataclass
class CompanyIntelRecord:
    company: str
    first_seen: str
    last_seen: str
    seen_count: int
    sources: List[str]
    users: List[str]

    def to_dict(self) -> Dict:
        return {
            "company": self.company,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "seen_count": self.seen_count,
            "sources": self.sources,
            "users": self.users,
        }


class CompanyIntelService:
    def __init__(self) -> None:
        self.paths = CareerTrojanPaths()
        self.registry_path = self.paths.ai_data_final / "metadata" / "company_intel_registry.json"
        self.events_path = self.paths.logs / "company_intel_events.jsonl"

    def _load_registry(self) -> Dict[str, Dict]:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_registry(self, registry: Dict[str, Dict]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    def _append_event(self, payload: Dict) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _load_events(self) -> List[Dict[str, Any]]:
        if not self.events_path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        try:
            lines = self.events_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        return rows

    def _extract_companies(self, text: str) -> List[str]:
        if not text:
            return []
        if extract_companies is not None:
            try:
                return [c.strip() for c in extract_companies(text) if str(c).strip()]
            except Exception:
                pass

        # Fallback heuristic
        import re

        patterns = [
            r"\b([A-Z][A-Za-z0-9&.,\- ]{2,80}(?:Ltd|Limited|Inc|Corporation|Corp|Company|Co|LLC|LLP|PLC|GmbH|AG|SA|Pvt))\b",
            r"\b([A-Z][A-Za-z0-9&.,\- ]{2,80}(?:Group|Holdings|International|Global|Solutions|Services|Systems|Technologies|Tech))\b",
        ]
        found: List[str] = []
        for pattern in patterns:
            found.extend(re.findall(pattern, text))
        return sorted({c.strip() for c in found if c.strip()})

    def ingest_resume_text(
        self,
        text: str,
        user_id: Optional[str] = None,
        source: str = "resume_upload",
    ) -> Dict[str, int]:
        companies = self._extract_companies(text)
        now = datetime.utcnow().isoformat() + "Z"
        registry = self._load_registry()

        added = 0
        updated = 0
        for company in companies:
            key = company.lower()
            current = registry.get(key)
            if not current:
                record = CompanyIntelRecord(
                    company=company,
                    first_seen=now,
                    last_seen=now,
                    seen_count=1,
                    sources=[source],
                    users=[user_id] if user_id else [],
                )
                registry[key] = record.to_dict()
                added += 1
            else:
                current["last_seen"] = now
                current["seen_count"] = int(current.get("seen_count", 0)) + 1
                current_sources = set(current.get("sources") or [])
                current_sources.add(source)
                current["sources"] = sorted(current_sources)
                if user_id:
                    current_users = set(current.get("users") or [])
                    current_users.add(user_id)
                    current["users"] = sorted(current_users)
                registry[key] = current
                updated += 1

        self._save_registry(registry)
        self._append_event(
            {
                "timestamp": now,
                "source": source,
                "user_id": user_id,
                "companies_found": len(companies),
                "companies_added": added,
                "companies_updated": updated,
            }
        )

        return {
            "companies_found": len(companies),
            "companies_added": added,
            "companies_updated": updated,
        }

    def list_registry(self, limit: int = 100, query: Optional[str] = None) -> List[Dict]:
        registry = self._load_registry()
        rows = list(registry.values())

        if query:
            q = query.strip().lower()
            rows = [
                row for row in rows
                if q in str(row.get("company", "")).lower()
            ]

        rows.sort(
            key=lambda row: (
                int(row.get("seen_count", 0)),
                str(row.get("last_seen", "")),
            ),
            reverse=True,
        )
        return rows[: max(1, min(limit, 2000))]

    def get_registry_summary(self) -> Dict[str, int]:
        registry = self._load_registry()
        total_companies = len(registry)
        total_seen = sum(int(row.get("seen_count", 0)) for row in registry.values())
        return {
            "total_companies": total_companies,
            "total_seen_events": total_seen,
        }

    def list_recent_events(
        self,
        limit: int = 50,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_events()

        if source:
            source_needle = source.strip().lower()
            rows = [
                row for row in rows
                if source_needle == str(row.get("source", "")).strip().lower()
            ]

        if user_id:
            user_needle = user_id.strip().lower()
            rows = [
                row for row in rows
                if user_needle == str(row.get("user_id", "")).strip().lower()
            ]

        rows.sort(key=lambda row: str(row.get("timestamp", "")), reverse=True)
        return rows[: max(1, min(limit, 5000))]

    def get_registry_analytics(self, limit: int = 20, event_limit: int = 200) -> Dict[str, Any]:
        registry = self._load_registry()
        events = self.list_recent_events(limit=max(1, min(event_limit, 10000)))

        rows = list(registry.values())
        rows.sort(
            key=lambda row: (
                int(row.get("seen_count", 0)),
                str(row.get("last_seen", "")),
            ),
            reverse=True,
        )

        top_companies = rows[: max(1, min(limit, 200))]
        source_counts = Counter(
            source
            for row in rows
            for source in (row.get("sources") or [])
            if str(source).strip()
        )
        user_counts = Counter(
            user
            for row in rows
            for user in (row.get("users") or [])
            if str(user).strip()
        )
        active_days = Counter(
            str(event.get("timestamp", "")).split("T", 1)[0]
            for event in events
            if str(event.get("timestamp", "")).strip()
        )

        return {
            "summary": self.get_registry_summary(),
            "top_companies": top_companies,
            "source_counts": [
                {"source": source, "count": count}
                for source, count in source_counts.most_common(25)
            ],
            "user_activity": [
                {"user_id": user_id, "count": count}
                for user_id, count in user_counts.most_common(25)
            ],
            "active_days": [
                {"date": day, "events": count}
                for day, count in active_days.most_common(60)
            ],
            "recent_events": events,
        }


_service: Optional[CompanyIntelService] = None


def get_company_intel_service() -> CompanyIntelService:
    global _service
    if _service is None:
        _service = CompanyIntelService()
    return _service
