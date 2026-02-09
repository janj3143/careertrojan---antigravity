"""
AI/NLP Extraction Module: Extracts companies, roles, products, locations, and relationships using spaCy.
"""
import spacy
from typing import Dict, List

# Load spaCy model (en_core_web_sm for demo; use en_core_web_trf for production)
nlp = spacy.load("en_core_web_sm")

ENTITY_LABELS = ["ORG", "PERSON", "GPE", "PRODUCT", "LOC", "EVENT"]

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities and relationships from text using spaCy NLP.
    Returns a dict with entity types as keys and lists of unique entities as values.
    """
    doc = nlp(text)
    entities = {label: set() for label in ENTITY_LABELS}
    for ent in doc.ents:
        if ent.label_ in ENTITY_LABELS:
            entities[ent.label_].add(ent.text.strip())
    # Convert sets to sorted lists
    return {label: sorted(list(vals)) for label, vals in entities.items() if vals}

# Example usage (for testing):
if __name__ == "__main__":
    sample = "Apple Inc. acquired Beats Electronics in California. Elon Musk leads SpaceX."
    print(extract_entities(sample))
