"""
Glossary Service - Optimized
"""
import json
from pathlib import Path
from typing import List, Optional

from services.shared.paths import CareerTrojanPaths

def load_glossary(glossary_path: Path) -> dict:
    if glossary_path.exists():
        with open(glossary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_term_definition(glossary: dict, term: str) -> str:
    return glossary.get(term, "Definition not found.")


def load_collocation_glossary(glossary_path: Optional[Path] = None) -> dict:
    if glossary_path is None:
        glossary_path = CareerTrojanPaths().ai_data_final / "collocations_glossary.json"
    if glossary_path.exists():
        with open(glossary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_collocation_phrases(glossary_path: Optional[Path] = None) -> List[str]:
    glossary = load_collocation_glossary(glossary_path)
    phrases: List[str] = []
    for item in glossary.get("bigrams", []):
        phrase = item.get("phrase") if isinstance(item, dict) else None
        if phrase:
            phrases.append(phrase)
    for item in glossary.get("trigrams", []):
        phrase = item.get("phrase") if isinstance(item, dict) else None
        if phrase:
            phrases.append(phrase)
    for item in glossary.get("glossary_terms", []):
        term = item.get("term") if isinstance(item, dict) else None
        if term:
            phrases.append(term)
    return list(dict.fromkeys(phrases))
