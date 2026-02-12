"""
Clean and finalize the extracted collocations.
Removes noise, normalizes terms, ensures minimum quality.
"""
import json
import re

INPUT = r"C:\careertrojan\data\ai_data_final\gazetteers\classification_collocations.json"
OUTPUT = INPUT  # overwrite

# Noise patterns to remove
REMOVE_PATTERNS = [
    r'^ADD term',          # editorial notes
    r'^See also',
    r'^See \d',
    r'SOC[-\s]ext code',
    r'^\d{4}/\d{2}',       # SOC code refs
    r'<[a-z]',             # HTML tags
    r'style=',             # CSS
    r'padding',
    r'\bdt\b.*style',
    r'^\d+\s+technician$', # bare numbered technician
    r'^1st Class$',
    r'ManufacturingT$',    # artifact trailing T
    r'ServicesT$',
    r'TransportationT$',
    r'ProcessingT$',
    r'ProductionT$',
    r'MillsT$',
    r'FoundriesT$',
    r'MiningT$',
    r'TradeT$',
    r'RepairT$',
    r'T$',                 # trailing T artifacts from NAICS
    r'^\w{1,2}\s+\w{1,2}$', # too short like "2a BC"
    r'^accounting for one-half',
    r'^a general line',
    r'^a location designated',
    r'^acting as agents',
    r'^and\s+',            # starts with "and"
    r'^or\s+',             # starts with "or"
    r'^the\s+',            # starts with "the" 
    r'^that\s+',
    r'^which\s+',
    r'^for\s+',
    r'^in\s+the\s+',
    r'^such\s+as',
    r'^including\s+',
    r'^but\s+not',
    r'^except\s+',
    r'^also\s+',
    r'^primarily\s+',
    r'^mainly\s+',
    r'^as\s+well\s+as',
    r'^not\s+',
    r'^\d+\.\d+',         # decimal numbers
    r'^establishments\s',
    r'one-half',
    r'primarily engaged',
    r'engaged in',
    r'known as',
    r'classified in',
    r'classified elsewhere',
    r'classified under',
    r'are classified',
    r'may also',
    r'n\.e\.c',            # not elsewhere classified - keep some though
]

REMOVE_RE = re.compile('|'.join(REMOVE_PATTERNS), re.IGNORECASE)

def clean_trailing_T(term):
    """Remove the trailing T that NAICS frequently has as an artifact."""
    # e.g., "Abrasive Product ManufacturingT" -> "Abrasive Product Manufacturing"
    if term.endswith('T') and len(term) > 5:
        base = term[:-1]
        # Only strip if the base looks like a normal phrase
        if base[-1].islower() or base.endswith('ing') or base.endswith('ion') or base.endswith('es'):
            return base
    return term

def is_quality_term(term):
    """Check if a term meets quality thresholds."""
    if not term or len(term) < 5:
        return False
    
    # Must be multi-word
    words = term.split()
    if len(words) < 2:
        return False
    
    # Not too long (probably a sentence)
    if len(words) > 8:
        return False
    
    # Check noise patterns
    if REMOVE_RE.search(term):
        return False
    
    # Must be mostly alphabetic
    alpha = sum(1 for c in term if c.isalpha())
    if alpha < len(term) * 0.5:
        return False
    
    # Skip pure numbers with a word
    if re.match(r'^\d+\s+\w+$', term) and len(words) == 2:
        # Allow "3d artist" type but not "111 adviser"
        first = words[0]
        if len(first) > 2 and first.isdigit():
            return False
    
    return True

def normalize_term(term):
    """Normalize a term for consistent format."""
    t = term.strip()
    t = re.sub(r'\s+', ' ', t)
    # Remove trailing punctuation
    t = re.sub(r'[,;:\.\!]+$', '', t)
    # Remove leading articles sometimes
    # Keep "The" for proper nouns
    # Clean up possessives and abbreviations are fine
    # Trim the trailing T artifact
    t = clean_trailing_T(t)
    return t.strip()

def main():
    with open(INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned = {}
    total_before = 0
    total_after = 0
    
    for cat, terms in data.items():
        total_before += len(terms)
        good = set()
        for term in terms:
            t = normalize_term(term)
            if is_quality_term(t):
                good.add(t)
        cleaned[cat] = sorted(good, key=str.lower)
        total_after += len(cleaned[cat])
        print(f"{cat}: {len(terms)} -> {len(cleaned[cat])}")
    
    # Save
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal: {total_before} -> {total_after}")
    print(f"Saved: {OUTPUT}")
    
    # Print samples for each category
    for cat in sorted(cleaned.keys()):
        items = cleaned[cat]
        print(f"\n=== {cat} ({len(items)} terms) ===")
        for t in items[:30]:
            print(f"  {t}")
        if len(items) > 30:
            print(f"  ... ({len(items) - 30} more)")

if __name__ == "__main__":
    main()
