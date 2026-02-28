#!/usr/bin/env python3
"""
Enhance Training Data
=====================
Builds enrichment artefacts from collocation_data and writes outputs consumed
by training workflows.

Outputs:
- ai_data_final/metadata/enhanced_keywords.json
- ai_data_final/metadata/enriched_knowledge_graph.json
- ai_data_final/metadata/expanded_case_base.json
- ai_data_final/metadata/enhance_training_data_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths


@dataclass
class CollocationBucket:
    technical: List[str]
    management: List[str]
    companies: List[str]
    job_titles: List[str]
    skills: List[str]


TECH_HINTS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "docker",
    "kubernetes",
    "sql",
    "postgresql",
    "fastapi",
    "react",
    "tensorflow",
    "machine learning",
    "data engineering",
    "cloud",
    "devops",
}

MGMT_HINTS = {
    "manager",
    "director",
    "executive",
    "lead",
    "head",
    "strategy",
    "operations",
    "stakeholder",
    "roadmap",
    "budget",
}


def _safe_load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_all_collocations(collocation_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    payload: Dict[str, List[Dict[str, Any]]] = {}
    if not collocation_dir.exists():
        return payload

    for file_path in collocation_dir.glob("*.json"):
        data = _safe_load_json(file_path, [])
        if isinstance(data, list):
            payload[file_path.stem] = [row for row in data if isinstance(row, dict)]
    return payload


def _extract_phrase(row: Dict[str, Any]) -> str:
    phrase = str(row.get("phrase") or row.get("term") or "").strip().lower()
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase


def build_enhanced_keywords(
    collocations: Dict[str, List[Dict[str, Any]]],
    max_rows_per_file: int = 250000,
) -> Dict[str, List[str]]:
    technical: set = set()
    management: set = set()
    companies: set = set()
    job_titles: set = set()
    skills: set = set()

    for rows in collocations.values():
        for row in rows[:max_rows_per_file]:
            phrase = _extract_phrase(row)
            if len(phrase) < 2 or len(phrase) > 120:
                continue

            label = str(row.get("label") or "").lower()
            confidence = float(row.get("confidence") or 0.0)
            if confidence and confidence < 0.5:
                continue

            if "company" in label:
                companies.add(phrase)
            if "job" in label or "title" in label:
                job_titles.add(phrase)
            if "skill" in label:
                skills.add(phrase)

            # inferred buckets
            if any(hint in phrase for hint in TECH_HINTS):
                technical.add(phrase)
            if any(hint in phrase for hint in MGMT_HINTS):
                management.add(phrase)

    # fold skills/job titles into high-value sets where relevant
    for value in skills:
        if any(hint in value for hint in TECH_HINTS):
            technical.add(value)
    for value in job_titles:
        if any(hint in value for hint in MGMT_HINTS):
            management.add(value)

    return {
        "technical": sorted(technical),
        "management": sorted(management),
        "companies": sorted(companies),
        "job_titles": sorted(job_titles),
        "skills": sorted(skills),
    }


def enrich_knowledge_graph(keywords: Dict[str, List[str]]) -> Dict[str, Any]:
    nodes: Dict[str, Dict[str, str]] = {}
    edges: List[Dict[str, str]] = []

    def add_node(node_id: str, node_type: str) -> None:
        nodes[node_id] = {"id": node_id, "type": node_type}

    for company in keywords["companies"]:
        add_node(company, "company")
    for title in keywords["job_titles"]:
        add_node(title, "job_title")
    for skill in keywords["skills"]:
        add_node(skill, "skill")

    # lightweight associations based on token overlap
    title_tokens = {title: set(title.split()) for title in keywords["job_titles"]}
    skill_tokens = {skill: set(skill.split()) for skill in keywords["skills"]}

    for title, t_tokens in title_tokens.items():
        for skill, s_tokens in skill_tokens.items():
            if not t_tokens or not s_tokens:
                continue
            if t_tokens.intersection(s_tokens):
                edges.append({"from": title, "to": skill, "relation": "related_skill"})

    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def expand_case_base(keywords: Dict[str, List[str]]) -> Dict[str, Any]:
    archetypes: List[Dict[str, Any]] = []

    industry_groups = {
        "technology": ["engineer", "developer", "data", "cloud", "devops"],
        "operations": ["operations", "logistics", "supply chain", "manager"],
        "commercial": ["sales", "account", "business development", "marketing"],
    }

    for group, hints in industry_groups.items():
        matching_titles = [
            title for title in keywords["job_titles"]
            if any(hint in title for hint in hints)
        ][:100]

        matching_skills = [
            skill for skill in keywords["skills"]
            if any(hint in skill for hint in hints)
        ][:150]

        archetypes.append(
            {
                "industry_group": group,
                "sample_titles": matching_titles,
                "sample_skills": matching_skills,
                "recommended_focus": f"{group}_career_path",
            }
        )

    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "archetype_count": len(archetypes),
        },
        "archetypes": archetypes,
    }


def generate_salary_derivation_code() -> str:
    return '''
def derive_salary_estimate(row: dict) -> float:
    title = (row.get("job_title") or "").lower()
    years = float(row.get("experience_years") or 0)
    skills = len(row.get("skills") or [])

    base = 28000.0
    if any(x in title for x in ["senior", "lead", "principal", "head", "director"]):
        base += 18000
    if any(x in title for x in ["manager", "executive"]):
        base += 12000
    if any(x in title for x in ["data", "machine learning", "devops", "cloud"]):
        base += 8000

    base += years * 1800
    base += min(skills, 25) * 350

    return round(max(22000.0, min(base, 220000.0)), 2)


def derive_match_score(row: dict) -> float:
    years = float(row.get("experience_years") or 0)
    skills = len(row.get("skills") or [])

    score = 0.15
    score += min(years / 15.0, 0.45)
    score += min(skills / 30.0, 0.35)

    title = (row.get("job_title") or "").lower()
    if any(x in title for x in ["senior", "lead", "principal", "manager"]):
        score += 0.08

    return round(min(max(score, 0.05), 0.99), 4)
'''


def generate_data_loader_patch() -> str:
    return """
# PATCH GUIDANCE: services/ai_engine/data_loader.py
# 1) Add enhanced keyword loader near module imports:

from services.shared.paths import CareerTrojanPaths

def _load_enhanced_keywords() -> dict:
    paths = CareerTrojanPaths()
    target = paths.ai_data_final / "metadata" / "enhanced_keywords.json"
    if not target.exists():
        return {}
    try:
        import json
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}

_ENHANCED_KW = _load_enhanced_keywords()

# 2) In get_terms(), merge in _ENHANCED_KW["skills"] for richer term cloud.
""".strip()


def generate_train_all_models_patch() -> str:
    return """
# PATCH GUIDANCE: services/ai_engine/train_all_models.py
# 1) Import derivation helpers from generated metadata module
#    or inline the derive_salary_estimate / derive_match_score functions.
# 2) Replace random salary/match fallback generation with deterministic derivation
#    based on job_title + experience_years + skill count.
""".strip()


def write_json(path: Path, payload: Any, apply: bool) -> None:
    if not apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate enhanced training artefacts")
    parser.add_argument("--apply", action="store_true", help="Write generated files")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=250000,
        help="Max rows to process from each collocation JSON file",
    )
    args = parser.parse_args()

    paths = CareerTrojanPaths()
    collocation_dir = paths.ai_data_final / "collocation_data"
    metadata_dir = paths.ai_data_final / "metadata"

    collocations = load_all_collocations(collocation_dir)
    keywords = build_enhanced_keywords(
        collocations,
        max_rows_per_file=max(1000, args.max_rows_per_file),
    )
    knowledge_graph = enrich_knowledge_graph(keywords)
    case_base = expand_case_base(keywords)

    salary_code = generate_salary_derivation_code()
    data_loader_patch = generate_data_loader_patch()
    train_patch = generate_train_all_models_patch()

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "apply": args.apply,
        "collocation_files": sorted(collocations.keys()),
        "counts": {
            "technical_keywords": len(keywords["technical"]),
            "management_keywords": len(keywords["management"]),
            "companies": len(keywords["companies"]),
            "job_titles": len(keywords["job_titles"]),
            "skills": len(keywords["skills"]),
            "knowledge_graph_nodes": knowledge_graph["metadata"]["node_count"],
            "knowledge_graph_edges": knowledge_graph["metadata"]["edge_count"],
            "archetypes": case_base["metadata"]["archetype_count"],
        },
        "paths": {
            "enhanced_keywords": str(metadata_dir / "enhanced_keywords.json"),
            "knowledge_graph": str(metadata_dir / "enriched_knowledge_graph.json"),
            "case_base": str(metadata_dir / "expanded_case_base.json"),
            "salary_derivation_code": str(metadata_dir / "salary_derivation_code.py"),
            "report": str(metadata_dir / "enhance_training_data_report.json"),
        },
        "patch_guidance": {
            "data_loader": data_loader_patch,
            "train_all_models": train_patch,
        },
    }

    write_json(metadata_dir / "enhanced_keywords.json", keywords, args.apply)
    write_json(metadata_dir / "enriched_knowledge_graph.json", knowledge_graph, args.apply)
    write_json(metadata_dir / "expanded_case_base.json", case_base, args.apply)
    write_json(metadata_dir / "enhance_training_data_report.json", report, args.apply)

    if args.apply:
        (metadata_dir / "salary_derivation_code.py").write_text(salary_code, encoding="utf-8")

    if args.verbose:
        print(json.dumps(report, indent=2))
    else:
        print(
            json.dumps(
                {
                    "apply": args.apply,
                    "technical_keywords": len(keywords["technical"]),
                    "management_keywords": len(keywords["management"]),
                    "companies": len(keywords["companies"]),
                    "job_titles": len(keywords["job_titles"]),
                    "skills": len(keywords["skills"]),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
