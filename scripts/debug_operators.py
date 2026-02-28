"""Debug: why do negation + span export find 0 matches?"""
import sys, os, re
sys.path.insert(0, r"C:\careertrojan")
os.chdir(r"C:\careertrojan")

from services.ai_engine.collocation_engine import CollocationEngine

e = CollocationEngine(min_freq=1, pmi_threshold=1.0, window_size=5)
print(f"known_phrases count: {len(e.known_phrases)}")
sample = sorted(list(e.known_phrases))[:15]
print(f"sample: {sample}")

# Manual regex test
targets = e.known_phrases
sorted_targets = sorted(targets, key=len, reverse=True)
pattern_str = "|".join(re.escape(p) for p in sorted_targets[:5000])
print(f"\nregex pattern length: {len(pattern_str)} chars")
print(f"first 300 chars: {pattern_str[:300]}")

phrase_re = re.compile(rf"\b(?:{pattern_str})\b", re.IGNORECASE)

texts = [
    "Experienced in machine learning and deep learning for industrial automation.",
    "No experience in data science. Never used Python for cloud computing.",
    "Strong background in project management, not machine learning.",
    "Blue Hydrogen and Green Hydrogen are key energy technologies.",
]
for i, text in enumerate(texts):
    matches = list(phrase_re.finditer(text))
    print(f"\ntext[{i}]: {text[:80]}...")
    print(f"  matches: {[(m.group(), m.start(), m.end()) for m in matches]}")

# Now test via actual method
print("\n=== tag_negations ===")
neg = e.tag_negations(texts)
print(f"result: {len(neg)} phrases")
for phrase, spans in neg.items():
    print(f"  '{phrase}': {len(spans)} spans")

print("\n=== extract_phrase_spans ===")
sp = e.extract_phrase_spans(texts)
print(f"result: {len(sp)} phrases")
for phrase, spans in sp.items():
    print(f"  '{phrase}': {len(spans)} spans")
