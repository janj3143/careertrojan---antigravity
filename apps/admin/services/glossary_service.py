"""
Glossary Service - Optimized
"""
import json
from pathlib import Path

def load_glossary(glossary_path: Path) -> dict:
    if glossary_path.exists():
        with open(glossary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_term_definition(glossary: dict, term: str) -> str:
    return glossary.get(term, "Definition not found.")
