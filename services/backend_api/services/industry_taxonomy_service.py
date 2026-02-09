"""
Industry Taxonomy Service for IntelliCV-AI
==========================================

This module centralises loading and querying of *real* industry and
occupation taxonomies so that:

- User portal (job optimiser, mentorship, coaching hub)
- Admin portal (job cloud, overlap analytics)
- AI enrichment pipeline

can all talk to **one consistent source of truth** for:
  • UK SOC 2020 (Standard Occupational Classification)
  • ESCO (European Skills, Competences, Qualifications and Occupations)
  • NAICS 2022 (North American Industry Classification System)

The goal is to give you:

  IndustryTaxonomyService  → lightweight service with:
    - .load_soc2020()
    - .load_esco()
    - .load_naics()
    - .infer_industry_for_job_title(job_title, hints=...)
    - .infer_codes_for_job_title(job_title)

The service is **file-backed** and **real-data only**:
  - If a dataset path is missing, the loader fails *gracefully*.
  - No dummy rows or fallback demo content are ever fabricated here.

You should wire this module into:

  - 18_Job_Title_AI_Integration.py
  - 19_Job_Title_Overlap_Cloud.py
  - 17_Mentor_Management.py

by importing IndustryTaxonomyService and using it wherever you need
to resolve industries, job families, or codes.

NOTE: All paths are configurable via environment variables so that
Docker, dev, and admin environments can share the same code.

Env variables (recommended):
  INTELLICV_DATA_ROOT               – base path for large taxonomies
  INTELLICV_SOC2020_STRUCTURE       – override for SOC 2020 structure Excel
  INTELLICV_SOC2020_INDEX           – override for SOC 2020 coding index Excel
  INTELLICV_ESCO_CLASSIFICATION     – path to ESCO classification CSV
  INTELLICV_NAICS_STRUCTURE         – NAICS 2022 structure Excel
  INTELLICV_NAICS_DESCRIPTIONS      – NAICS 2022 descriptions Excel

The module is intentionally conservative: it only *reads* from disk
and returns Python objects; higher-level aggregation stays in portal
pages or admin analytics.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


# ---------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------
@dataclass
class IndustryNode:
    code: str
    name: str
    taxonomy: str  # "SOC2020", "ESCO", "NAICS2022"
    level: Optional[str] = None  # e.g. "Major Group", "Division"
    parent_code: Optional[str] = None
    description: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "taxonomy": self.taxonomy,
            "level": self.level,
            "parent_code": self.parent_code,
            "description": self.description,
        }


@dataclass
class JobIndustryMatch:
    job_title: str
    normalized_title: str
    source: str  # "SOC2020", "ESCO", "NAICS2022", "JOB_DB"
    score: float
    codes: List[str]
    industries: List[IndustryNode]


# ---------------------------------------------------------------------
# Main Service
# ---------------------------------------------------------------------
class IndustryTaxonomyService:
    """
    Central industry taxonomy loader and resolver.

    Usage (typical):

        svc = IndustryTaxonomyService()
        svc.load_all_if_needed()

        match = svc.infer_industry_for_job_title("Senior Data Scientist")
        if match:
            print(match.industries[0].name)

    """

    def __init__(
        self,
        data_root: Optional[Path] = None,
        soc_structure_path: Optional[Path] = None,
        soc_index_path: Optional[Path] = None,
        esco_path: Optional[Path] = None,
        naics_structure_path: Optional[Path] = None,
        naics_desc_path: Optional[Path] = None,
    ) -> None:
        # Default to env var or portable local path
        default_root = os.environ.get("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final/ai_data_final")
        
        self.data_root = (
            Path(data_root)
            if data_root
            else Path(os.environ.get("INTELLICV_DATA_ROOT", default_root)).expanduser()
        )

        # Allow explicit overrides; otherwise derive from data_root if present
        self.soc_structure_path = self._resolve_path(
            soc_structure_path,
            env_var="INTELLICV_SOC2020_STRUCTURE",
            default_filename="extendedsoc2020structureanddescriptionsexcel03122025.xlsx",
        )
        self.soc_index_path = self._resolve_path(
            soc_index_path,
            env_var="INTELLICV_SOC2020_INDEX",
            default_filename="soc2020volume2thecodingindexexcel03122025.xlsx",
        )
        self.esco_path = self._resolve_path(
            esco_path,
            env_var="INTELLICV_ESCO_CLASSIFICATION",
            default_filename="esco_classification_en.csv",
        )
        self.naics_structure_path = self._resolve_path(
            naics_structure_path,
            env_var="INTELLICV_NAICS_STRUCTURE",
            default_filename="2022_NAICS_Structure.xlsx",
        )
        self.naics_desc_path = self._resolve_path(
            naics_desc_path,
            env_var="INTELLICV_NAICS_DESCRIPTIONS",
            default_filename="2022_NAICS_Descriptions.xlsx",
        )

        # Internal caches
        self._soc_df: Optional[pd.DataFrame] = None
        self._soc_index_df: Optional[pd.DataFrame] = None
        self._esco_df: Optional[pd.DataFrame] = None
        self._naics_df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def _resolve_path(
        self,
        explicit: Optional[Path],
        env_var: str,
        default_filename: str,
    ) -> Optional[Path]:
        if explicit:
            return Path(explicit)

        # Environment override wins
        env_val = os.environ.get(env_var)
        if env_val:
            p = Path(env_val).expanduser()
            return p if p.exists() else None

        # If data_root is set, try default filename under it
        if self.data_root:
            candidate = self.data_root / default_filename
            if candidate.exists():
                return candidate

        return None

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    def load_all_if_needed(self) -> None:
        self.load_soc2020()
        self.load_esco()
        self.load_naics()

    def load_soc2020(self) -> None:
        if self._soc_df is not None and self._soc_index_df is not None:
            return

        if not self.soc_structure_path or not self.soc_structure_path.exists():
            return
        if not self.soc_index_path or not self.soc_index_path.exists():
            return

        try:
            self._soc_df = pd.read_excel(self.soc_structure_path)
        except Exception:
            self._soc_df = None

        try:
            self._soc_index_df = pd.read_excel(self.soc_index_path)
        except Exception:
            self._soc_index_df = None

    def load_esco(self) -> None:
        if self._esco_df is not None:
            return
        if not self.esco_path or not self.esco_path.exists():
            return

        try:
            # ESCO classification CSV from official release
            self._esco_df = pd.read_csv(self.esco_path)
        except Exception:
            self._esco_df = None

    def load_naics(self) -> None:
        if self._naics_df is not None:
            return
        if not self.naics_structure_path or not self.naics_structure_path.exists():
            return

        try:
            df_struct = pd.read_excel(self.naics_structure_path)
        except Exception:
            self._naics_df = None
            return

        # Optionally enrich with descriptions
        if self.naics_desc_path and self.naics_desc_path.exists():
            try:
                df_desc = pd.read_excel(self.naics_desc_path)
                # Attempt to merge on "Code"/"NAICS Code" style columns
                join_cols = [
                    ("NAICS Code", "NAICS Code"),
                    ("Code", "Code"),
                    ("2017 NAICS Code", "2022 NAICS Code"),
                    ("2022 NAICS Code", "2022 NAICS Code"),
                ]
                merged = None
                for left, right in join_cols:
                    if left in df_struct.columns and right in df_desc.columns:
                        merged = df_struct.merge(
                            df_desc, left_on=left, right_on=right, how="left"
                        )
                        break
                self._naics_df = merged if merged is not None else df_struct
            except Exception:
                self._naics_df = df_struct
        else:
            self._naics_df = df_struct

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------
    def infer_industry_for_job_title(
        self,
        job_title: str,
        hints: Optional[Dict[str, Any]] = None,
        max_results: int = 3,
    ) -> Optional[JobIndustryMatch]:
        """
        Heuristic resolver across SOC / ESCO / NAICS.

        Strategy (simple, but real-data-backed):

        1. Normalise the job title (casefold, strip punctuation).
        2. Try ESCO occupation labels (they are occupation-focused).
        3. Fall back to SOC index (UK-specific).
        4. Optionally look at NAICS titles (industry-leaning).

        Returns the *best single* JobIndustryMatch, or None.
        """
        title = job_title.strip()
        if not title:
            return None

        norm = self._normalise_title(title)
        self.load_all_if_needed()

        candidates: List[JobIndustryMatch] = []

        # ESCO: preferredLabel / altLabels contain occupations and sectors
        esco_matches = self._match_esco(norm, max_results=max_results)
        candidates.extend(esco_matches)

        # SOC 2020: use coding index (job titles → SOC code → Major Group)
        soc_matches = self._match_soc(norm, max_results=max_results)
        candidates.extend(soc_matches)

        # NAICS: match by title / description, but lower weight (industry code)
        naics_matches = self._match_naics(norm, max_results=max_results)
        candidates.extend(naics_matches)

        if not candidates:
            return None

        # Keep highest scoring candidate
        best = sorted(candidates, key=lambda m: m.score, reverse=True)[0]
        return best

    def infer_codes_for_job_title(
        self,
        job_title: str,
    ) -> Dict[str, List[str]]:
        """
        Convenience helper returning raw code lists for the three taxonomies.
        Useful when admin / overlap cloud wants codes only.
        """
        match = self.infer_industry_for_job_title(job_title)
        if not match:
            return {"SOC2020": [], "ESCO": [], "NAICS2022": []}

        codes_by_taxonomy: Dict[str, List[str]] = {
            "SOC2020": [],
            "ESCO": [],
            "NAICS2022": [],
        }
        for ind in match.industries:
            codes_by_taxonomy.setdefault(ind.taxonomy, []).append(ind.code)

        return codes_by_taxonomy

    # ------------------------------------------------------------------
    # Internal matching – ESCO / SOC / NAICS
    # ------------------------------------------------------------------
    def _normalise_title(self, title: str) -> str:
        t = title.lower()
        t = re.sub(r"[^a-z0-9\s\/&+\-]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _match_esco(
        self,
        norm_title: str,
        max_results: int = 3,
    ) -> List[JobIndustryMatch]:
        if self._esco_df is None:
            return []

        df = self._esco_df
        cols = {c.lower(): c for c in df.columns}

        label_col = cols.get("preferredlabel") or cols.get("preferred_label")
        if not label_col:
            return []

        # Basic string containment scoring
        scores: List[Tuple[float, int]] = []  # (score, row_idx)
        labels = df[label_col].astype(str).fillna("")
        for idx, label in labels.items():
            norm_label = self._normalise_title(label)
            if not norm_label:
                continue
            if norm_title == norm_label:
                score = 1.0
            elif norm_title in norm_label or norm_label in norm_title:
                score = 0.8
            else:
                continue
            scores.append((score, idx))

        scores.sort(reverse=True, key=lambda x: x[0])
        scores = scores[:max_results]

        matches: List[JobIndustryMatch] = []
        for score, idx in scores:
            row = df.loc[idx]
            code = str(row.get(cols.get("concepttype", "")) or row.get("conceptUri") or "")
            label_val = str(row.get(label_col) or "")
            # ESCO is occupation taxonomy – industry is not explicit;
            # you can extend this later with ESCO sector mapping.
            industry_node = IndustryNode(
                code=code or label_val,
                name=label_val,
                taxonomy="ESCO",
                level=None,
                parent_code=None,
                description=str(row.get("description", "")),
            )
            matches.append(
                JobIndustryMatch(
                    job_title=norm_title,
                    normalized_title=norm_title,
                    source="ESCO",
                    score=score,
                    codes=[industry_node.code],
                    industries=[industry_node],
                )
            )
        return matches

    def _match_soc(
        self,
        norm_title: str,
        max_results: int = 3,
    ) -> List[JobIndustryMatch]:
        if self._soc_index_df is None:
            return []

        df = self._soc_index_df
        cols = {c.lower(): c for c in df.columns}

        # SOC index often has columns like "Job Title", "SOC2020 Code"
        title_col = cols.get("job title") or cols.get("title") or cols.get("example job titles")
        code_col = cols.get("soc2020 code") or cols.get("code") or cols.get("soc code")

        if not title_col or not code_col:
            return []

        scores: List[Tuple[float, int]] = []
        titles = df[title_col].astype(str).fillna("")
        for idx, title in titles.items():
            norm_label = self._normalise_title(title)
            if not norm_label:
                continue
            if norm_title == norm_label:
                score = 1.0
            elif norm_title in norm_label or norm_label in norm_title:
                score = 0.75
            else:
                continue
            scores.append((score, idx))

        scores.sort(reverse=True, key=lambda x: x[0])
        scores = scores[:max_results]

        self.load_soc2020()
        major_group_lookup: Dict[str, str] = {}
        if self._soc_df is not None:
            soc_cols = {c.lower(): c for c in self._soc_df.columns}
            code_col_soc = soc_cols.get("unit group code") or soc_cols.get("soc2020 code") or soc_cols.get("code")
            title_soc_col = soc_cols.get("unit group title") or soc_cols.get("title")
            if code_col_soc and title_soc_col:
                for _, row in self._soc_df.iterrows():
                    c = str(row.get(code_col_soc))
                    nm = str(row.get(title_soc_col))
                    if c and nm:
                        major_group_lookup[c] = nm

        matches: List[JobIndustryMatch] = []
        for score, idx in scores:
            row = df.loc[idx]
            code_val = str(row.get(code_col) or "")
            industry_name = major_group_lookup.get(code_val, "")
            industry_node = IndustryNode(
                code=code_val,
                name=industry_name or f"SOC 2020 – {code_val}",
                taxonomy="SOC2020",
                level=None,
                parent_code=None,
                description=None,
            )
            matches.append(
                JobIndustryMatch(
                    job_title=norm_title,
                    normalized_title=norm_title,
                    source="SOC2020",
                    score=score,
                    codes=[industry_node.code],
                    industries=[industry_node],
                )
            )
        return matches

    def _match_naics(
        self,
        norm_title: str,
        max_results: int = 3,
    ) -> List[JobIndustryMatch]:
        if self._naics_df is None:
            return []

        df = self._naics_df
        cols = {c.lower(): c for c in df.columns}

        # Common NAICS columns: "2022 NAICS Code", "2022 NAICS Title"
        title_col = (
            cols.get("2022 naics title")
            or cols.get("naics title")
            or cols.get("title")
        )
        code_col = (
            cols.get("2022 naics code")
            or cols.get("naics code")
            or cols.get("code")
        )

        if not title_col or not code_col:
            return []

        scores: List[Tuple[float, int]] = []
        titles = df[title_col].astype(str).fillna("")
        for idx, title in titles.items():
            norm_label = self._normalise_title(title)
            if not norm_label:
                continue
            if norm_title == norm_label:
                score = 0.7  # lower than SOC / ESCO because NAICS is industry
            elif norm_title in norm_label or norm_label in norm_title:
                score = 0.5
            else:
                continue
            scores.append((score, idx))

        scores.sort(reverse=True, key=lambda x: x[0])
        scores = scores[:max_results]

        matches: List[JobIndustryMatch] = []
        for score, idx in scores:
            row = df.loc[idx]
            code_val = str(row.get(code_col) or "")
            name_val = str(row.get(title_col) or "")
            industry_node = IndustryNode(
                code=code_val,
                name=name_val or f"NAICS {code_val}",
                taxonomy="NAICS2022",
                level=None,
                parent_code=None,
                description=None,
            )
            matches.append(
                JobIndustryMatch(
                    job_title=norm_title,
                    normalized_title=norm_title,
                    source="NAICS2022",
                    score=score,
                    codes=[industry_node.code],
                    industries=[industry_node],
                )
            )
        return matches


# Convenience factory for portals
_GLOBAL_SVC: Optional[IndustryTaxonomyService] = None


def get_global_industry_taxonomy_service() -> IndustryTaxonomyService:
    """
    Singleton-style accessor so that Streamlit / FastAPI code can do:

        from services.industry_taxonomy_service import get_global_industry_taxonomy_service

        svc = get_global_industry_taxonomy_service()
        match = svc.infer_industry_for_job_title("Senior ML Engineer")

    without having to manage their own instance.
    """
    global _GLOBAL_SVC
    if _GLOBAL_SVC is None:
        _GLOBAL_SVC = IndustryTaxonomyService()
        _GLOBAL_SVC.load_all_if_needed()
    return _GLOBAL_SVC
