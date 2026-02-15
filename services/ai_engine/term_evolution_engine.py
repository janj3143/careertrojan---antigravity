"""
CareerTrojan — Term Evolution & Nomenclature Lineage Engine
============================================================

Solves the MRP→ERP problem: industry nomenclature evolves over time, and
users (and AI) may not realize that three different names describe the
SAME progressive concept. This engine:

  1. Loads evolution chains from term_evolution.json
  2. Given ANY term in a chain, returns the full lineage
  3. Identifies complementary/transferable skills across evolved terms
  4. Surfaces career insights showing users how their existing skills
     connect to modern/emerging roles
  5. Auto-discovers potential new evolution links from user interaction data

Usage:
    from services.ai_engine.term_evolution_engine import evolution_engine

    # What does "MRP" connect to?
    chain = evolution_engine.resolve("material requirements planning")
    # → full chain: MRP → MRP II → ERP → iERP → Composable ERP

    # What skills transfer?
    skills = evolution_engine.get_transferable_skills("mrp")
    # → ["supply chain management", "inventory management", "production planning", ...]

    # Career pivot advice
    insight = evolution_engine.get_career_insight("personnel management")
    # → "Personnel managers became HR managers became People Ops leads..."

    # Find which chains a user's skills overlap
    overlaps = evolution_engine.find_user_evolution_paths(["risk management", "capital adequacy", "stress testing"])
    # → [basel_tiers, solvency_tiers]
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

# ── Data paths (same convention as collocation_engine.py) ────────────────
_DATA_ROOT = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
AI_DATA_DIR = _DATA_ROOT / "ai_data_final"
GAZETTEERS_DIR = AI_DATA_DIR / "gazetteers"
EVOLUTION_FILE = GAZETTEERS_DIR / "term_evolution.json"

_LOCAL_DATA_ROOT = Path(os.getenv("CAREERTROJAN_LOCAL_DATA", r"C:\careertrojan\data\ai_data_final"))
LOCAL_EVOLUTION_FILE = _LOCAL_DATA_ROOT / "gazetteers" / "term_evolution.json"


class TermEvolutionEngine:
    """
    Tracks how industry nomenclature evolves over time and links related
    concepts across eras. Enables the AI to:
    - Recognize that MRP, MRP II, and ERP are the same progressive concept
    - Show users which of their skills transfer to newer/emerging fields
    - Surface career insights about industry evolution
    - Auto-learn new evolution patterns from user data
    """

    def __init__(self):
        self._lock = Lock()

        # Core data structures
        self.chains: Dict[str, Dict[str, Any]] = {}  # chain_id → chain data
        self.domain_overlaps: List[Dict[str, Any]] = []

        # Inverted indexes for fast lookups
        self._term_to_chains: Dict[str, List[str]] = defaultdict(list)  # normalized_term → [chain_ids]
        self._abbrev_to_chains: Dict[str, List[str]] = defaultdict(list)  # abbreviation → [chain_ids]
        self._skill_to_chains: Dict[str, List[str]] = defaultdict(list)  # skill → [chain_ids]
        self._domain_to_chains: Dict[str, List[str]] = defaultdict(list)  # domain → [chain_ids]

        # User-discovered evolution candidates (persisted separately)
        self._discovered_links: List[Dict[str, Any]] = []

        # Auto-load on instantiation
        self.load()

    def load(self, filepath: Optional[Path] = None) -> int:
        """
        Load evolution chains from term_evolution.json.
        Tries L: drive first, then local mirror.
        Returns number of chains loaded.
        """
        paths_to_try = [filepath] if filepath else [EVOLUTION_FILE, LOCAL_EVOLUTION_FILE]

        for path in paths_to_try:
            if path and path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    chains = data.get("evolution_chains", [])
                    self.domain_overlaps = data.get("domain_overlaps", [])

                    for chain in chains:
                        chain_id = chain.get("chain_id")
                        if not chain_id:
                            continue
                        self.chains[chain_id] = chain
                        self._index_chain(chain)

                    logger.info(
                        "Loaded %d evolution chains + %d domain overlaps from %s",
                        len(self.chains), len(self.domain_overlaps), path
                    )
                    return len(self.chains)
                except Exception as e:
                    logger.warning("Failed to load evolution data from %s: %s", path, e)

        logger.info("No term_evolution.json found — evolution engine running empty (will learn)")
        return 0

    def _index_chain(self, chain: Dict[str, Any]):
        """Build inverted indexes for a single chain."""
        chain_id = chain["chain_id"]
        domain = chain.get("domain", "")

        # Index by domain
        self._domain_to_chains[domain].append(chain_id)

        # Index by every term in the lineage
        for entry in chain.get("lineage", []):
            term = entry.get("term", "").lower().strip()
            if term:
                self._term_to_chains[term].append(chain_id)
                # Also index individual words for fuzzy matching
                for word in term.split():
                    if len(word) > 3:
                        self._term_to_chains[word].append(chain_id)

            abbrev = entry.get("abbrev")
            if abbrev:
                self._abbrev_to_chains[abbrev.lower()].append(chain_id)

        # Index by complementary skills
        for skill in chain.get("complementary_skills", []):
            self._skill_to_chains[skill.lower()].append(chain_id)

    # ── Core Lookup Methods ──────────────────────────────────────────────

    def resolve(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Given ANY term (or abbreviation), find the evolution chain it belongs to.
        Returns the full chain with lineage, current term, career insight, etc.

        Examples:
            resolve("mrp") → MRP → MRP II → ERP chain
            resolve("Basel II") → Basel I → II → III chain
            resolve("personnel management") → HR evolution chain
        """
        normalized = term.lower().strip()

        # Direct term match
        chain_ids = self._term_to_chains.get(normalized, [])

        # Abbreviation match
        if not chain_ids:
            chain_ids = self._abbrev_to_chains.get(normalized, [])

        # Fuzzy: check if any chain term contains the search term
        if not chain_ids:
            for indexed_term, ids in self._term_to_chains.items():
                if normalized in indexed_term or indexed_term in normalized:
                    chain_ids.extend(ids)
                    break

        if not chain_ids:
            return None

        # Return the best (most specific) match
        chain_id = chain_ids[0]
        chain = self.chains.get(chain_id)
        if not chain:
            return None

        # Enrich with position info
        result = {**chain}
        for i, entry in enumerate(chain.get("lineage", [])):
            if normalized in entry.get("term", "").lower() or \
               normalized == (entry.get("abbrev") or "").lower():
                result["matched_position"] = i
                result["matched_term"] = entry["term"]
                result["is_current"] = entry.get("status") == "current"
                result["is_historical"] = entry.get("status") == "historical"
                result["is_emerging"] = entry.get("status") == "emerging"
                break

        return result

    def resolve_all(self, term: str) -> List[Dict[str, Any]]:
        """
        Like resolve() but returns ALL chains that contain the term.
        Useful when a term appears in multiple evolution chains.
        """
        normalized = term.lower().strip()
        chain_ids = set()

        # Direct matches
        chain_ids.update(self._term_to_chains.get(normalized, []))
        chain_ids.update(self._abbrev_to_chains.get(normalized, []))

        # Skill matches (term might be a skill that bridges chains)
        chain_ids.update(self._skill_to_chains.get(normalized, []))

        results = []
        for chain_id in chain_ids:
            chain = self.chains.get(chain_id)
            if chain:
                results.append(chain)

        return results

    def get_lineage(self, term: str) -> List[Dict[str, Any]]:
        """
        Get the ordered lineage for a term (oldest → newest).
        Returns list of {term, abbrev, era, status} dicts.
        """
        chain = self.resolve(term)
        if not chain:
            return []
        return chain.get("lineage", [])

    def get_current_term(self, term: str) -> Optional[str]:
        """
        Given any historical or emerging term, return the CURRENT
        active equivalent. E.g., "MRP" → "enterprise resource planning"
        """
        chain = self.resolve(term)
        if not chain:
            return None
        return chain.get("current_term")

    def get_career_insight(self, term: str) -> Optional[str]:
        """
        Get the career coaching insight for the chain containing this term.
        This is the human-readable advice the AI should surface to users.
        """
        chain = self.resolve(term)
        if not chain:
            return None
        return chain.get("career_insight")

    def get_transferable_skills(self, term: str) -> List[str]:
        """
        Get all complementary/transferable skills for the chain(s) containing
        this term. These are skills that transfer across the evolution.
        """
        chains = self.resolve_all(term)
        skills = set()
        for chain in chains:
            skills.update(chain.get("complementary_skills", []))
        return sorted(skills)

    # ── User Skill Analysis ──────────────────────────────────────────────

    def find_user_evolution_paths(
        self, user_skills: List[str], user_job_titles: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Given a user's skills and job titles, find ALL evolution chains
        that overlap with their profile. This reveals career paths they
        may not know exist.

        Returns chains sorted by relevance (number of matching skills).
        """
        normalized_skills = {s.lower().strip() for s in user_skills}
        normalized_titles = {t.lower().strip() for t in (user_job_titles or [])}
        all_terms = normalized_skills | normalized_titles

        chain_scores: Dict[str, int] = defaultdict(int)
        chain_matches: Dict[str, List[str]] = defaultdict(list)

        for term in all_terms:
            # Check direct chain term matches
            for chain_id in self._term_to_chains.get(term, []):
                chain_scores[chain_id] += 3  # Strong signal
                chain_matches[chain_id].append(f"term:{term}")

            # Check abbreviation matches
            for chain_id in self._abbrev_to_chains.get(term, []):
                chain_scores[chain_id] += 3
                chain_matches[chain_id].append(f"abbrev:{term}")

            # Check skill matches
            for chain_id in self._skill_to_chains.get(term, []):
                chain_scores[chain_id] += 1  # Weaker signal (skill overlap)
                chain_matches[chain_id].append(f"skill:{term}")

        # Build results sorted by score
        results = []
        for chain_id, score in sorted(chain_scores.items(), key=lambda x: -x[1]):
            chain = self.chains.get(chain_id)
            if chain:
                # Calculate coverage: what % of the chain's skills does the user have?
                chain_skills = set(s.lower() for s in chain.get("complementary_skills", []))
                user_overlap = normalized_skills & chain_skills
                coverage = len(user_overlap) / max(len(chain_skills), 1)

                # What skills is the user MISSING to advance in this chain?
                gap_skills = chain_skills - normalized_skills

                results.append({
                    "chain_id": chain_id,
                    "chain_name": chain.get("current_term", chain_id),
                    "domain": chain.get("domain", ""),
                    "relevance_score": score,
                    "skill_coverage": round(coverage, 2),
                    "matching_items": chain_matches[chain_id],
                    "skills_you_have": sorted(user_overlap),
                    "skills_to_develop": sorted(gap_skills)[:10],  # Top 10 gaps
                    "career_insight": chain.get("career_insight"),
                })

        return results

    def find_domain_overlaps(self, user_skills: List[str]) -> List[Dict[str, Any]]:
        """
        Find cross-domain overlaps relevant to the user's skills.
        These are bridge opportunities between industries.
        """
        normalized = {s.lower().strip() for s in user_skills}
        results = []

        for overlap in self.domain_overlaps:
            bridge = set(s.lower() for s in overlap.get("bridge_skills", []))
            matching = normalized & bridge
            if matching:
                results.append({
                    "overlap_id": overlap["overlap_id"],
                    "domains": overlap["domains"],
                    "description": overlap["description"],
                    "matching_bridge_skills": sorted(matching),
                    "coverage": round(len(matching) / max(len(bridge), 1), 2),
                })

        return sorted(results, key=lambda x: -x["coverage"])

    # ── Dynamic Evolution Discovery ─────────────────────────────────────

    def suggest_evolution_link(
        self, old_term: str, new_term: str, domain: str = "",
        evidence: str = "", source: str = "user_interaction"
    ) -> Dict[str, Any]:
        """
        Record a potential evolution link discovered from user data.
        These are candidates for human review and eventual addition to
        term_evolution.json.

        The system detects these when:
        - A user's CV contains an old term but their recent searches use a new term
        - Multiple users in the same industry show the same old→new pattern
        - Job postings start using a new term for what was previously called something else
        """
        with self._lock:
            link = {
                "old_term": old_term.lower().strip(),
                "new_term": new_term.lower().strip(),
                "domain": domain,
                "evidence": evidence,
                "source": source,
                "first_seen": datetime.now().isoformat(),
                "occurrences": 1,
            }

            # Check for existing suggestion
            for existing in self._discovered_links:
                if existing["old_term"] == link["old_term"] and \
                   existing["new_term"] == link["new_term"]:
                    existing["occurrences"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                    logger.info(
                        "Evolution link reinforced: %s → %s (occurrences: %d)",
                        old_term, new_term, existing["occurrences"]
                    )
                    return existing

            self._discovered_links.append(link)
            logger.info("New evolution link suggested: %s → %s", old_term, new_term)
            return link

    def detect_evolution_patterns(
        self, user_cv_terms: List[str], user_search_terms: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Compare a user's CV terms (what they HAVE) with their search terms
        (what they WANT) to detect potential evolution patterns.

        If a user's CV says "MRP" and they're searching for "ERP" jobs,
        that's a strong signal that they're aware of the evolution but
        may not have updated their CV terminology.
        """
        cv_set = {t.lower().strip() for t in user_cv_terms}
        search_set = {t.lower().strip() for t in user_search_terms}

        patterns = []

        for cv_term in cv_set:
            cv_chain = self.resolve(cv_term)
            if not cv_chain:
                continue

            for search_term in search_set:
                search_chain = self.resolve(search_term)
                if search_chain and search_chain.get("chain_id") == cv_chain.get("chain_id"):
                    # Same chain! The user is evolving along a known path
                    cv_pos = cv_chain.get("matched_position", 0)
                    search_chain_resolved = self.resolve(search_term)
                    search_pos = search_chain_resolved.get("matched_position", 0) if search_chain_resolved else 0

                    if search_pos > cv_pos:
                        patterns.append({
                            "type": "forward_evolution",
                            "cv_term": cv_term,
                            "search_term": search_term,
                            "chain_id": cv_chain["chain_id"],
                            "chain_name": cv_chain.get("current_term"),
                            "career_insight": cv_chain.get("career_insight"),
                            "skill_gaps": self._compute_skill_gap(cv_chain, cv_pos, search_pos),
                        })

        # Also detect cross-chain patterns (user skills in one domain, searching in another)
        for cv_term in cv_set:
            for search_term in search_set - cv_set:
                cv_chains = self.resolve_all(cv_term)
                search_chains = self.resolve_all(search_term)

                if cv_chains and search_chains:
                    # Check for domain overlaps
                    cv_domains = {c.get("domain") for c in cv_chains}
                    search_domains = {c.get("domain") for c in search_chains}

                    for overlap in self.domain_overlaps:
                        overlap_domains = set(overlap.get("domains", []))
                        if cv_domains & overlap_domains and search_domains & overlap_domains:
                            patterns.append({
                                "type": "cross_domain_bridge",
                                "cv_term": cv_term,
                                "search_term": search_term,
                                "bridge_domains": sorted(overlap_domains),
                                "bridge_skills": overlap.get("bridge_skills", []),
                                "description": overlap.get("description"),
                            })
                            break

        return patterns

    def _compute_skill_gap(
        self, chain: Dict[str, Any], from_pos: int, to_pos: int
    ) -> List[str]:
        """
        Given positions in a chain, find what skills are needed to bridge
        from the old term era to the new term era.
        """
        # For now, return all complementary skills as gap candidates
        # In future, could be refined by era-specific skill mapping
        return chain.get("complementary_skills", [])[:10]

    # ── Persistence ─────────────────────────────────────────────────────

    def persist_discovered_links(self) -> bool:
        """
        Save user-discovered evolution links to disk for review.
        """
        if not self._discovered_links:
            return True

        output_path = GAZETTEERS_DIR / "discovered_evolution_links.json"
        try:
            data = {
                "persisted_at": datetime.now().isoformat(),
                "link_count": len(self._discovered_links),
                "links": self._discovered_links,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Persisted %d discovered evolution links", len(self._discovered_links))
            return True
        except Exception as e:
            logger.error("Failed to persist evolution links: %s", e)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about loaded evolution data."""
        all_terms = set()
        all_skills = set()
        domains = set()

        for chain in self.chains.values():
            domains.add(chain.get("domain", ""))
            for entry in chain.get("lineage", []):
                all_terms.add(entry.get("term", ""))
            all_skills.update(chain.get("complementary_skills", []))

        return {
            "chains_loaded": len(self.chains),
            "total_lineage_terms": len(all_terms),
            "total_complementary_skills": len(all_skills),
            "domains": sorted(domains),
            "domain_overlaps": len(self.domain_overlaps),
            "discovered_links": len(self._discovered_links),
            "evolution_file": str(EVOLUTION_FILE),
        }

    # ── Convenience: Format for AI Prompt ────────────────────────────────

    def format_for_ai_context(self, term: str) -> str:
        """
        Format evolution information as a text block suitable for injection
        into an AI prompt. This gives the LLM context about nomenclature evolution.
        """
        chain = self.resolve(term)
        if not chain:
            return ""

        lines = [
            f"📊 TERM EVOLUTION CONTEXT: {chain.get('current_term', term)}",
            f"Domain: {chain.get('domain', 'general')}",
            "",
            "Lineage (oldest → newest):",
        ]

        for entry in chain.get("lineage", []):
            status_icon = {"historical": "⬜", "current": "🟢", "emerging": "🔵"}.get(
                entry.get("status", ""), "⬜"
            )
            abbrev = f" ({entry['abbrev']})" if entry.get("abbrev") else ""
            lines.append(f"  {status_icon} {entry['term']}{abbrev} — {entry.get('era', '?')}")

        insight = chain.get("career_insight")
        if insight:
            lines.extend(["", f"💡 Career Insight: {insight}"])

        skills = chain.get("complementary_skills", [])
        if skills:
            lines.extend(["", f"🔗 Transferable Skills: {', '.join(skills[:8])}"])

        return "\n".join(lines)


# ── Module-level singleton ───────────────────────────────────────────────
evolution_engine = TermEvolutionEngine()
