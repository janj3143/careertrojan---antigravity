"""Quick smoke test for NEAR / NOT / NOR / Phrase Span operators."""
import sys, os
sys.path.insert(0, r"C:\careertrojan")
os.chdir(r"C:\careertrojan")

from services.ai_engine.collocation_engine import CollocationEngine

e = CollocationEngine(min_freq=1, pmi_threshold=1.0, window_size=5)

texts = [
    "Experienced in machine learning and deep learning for industrial automation.",
    "No experience in data science. Never used Python for cloud computing.",
    "Strong background in project management, not machine learning.",
    "Blue Hydrogen and Green Hydrogen are key energy technologies.",
]

# Test NEAR
print("=" * 60)
print("NEAR PROXIMITY OPERATOR")
print("=" * 60)
near_res, hits = e.find_near_pairs(texts, window=5, min_hits=1, top_k=20)
print(f"  Pairs: {len(near_res)}, Hits: {len(hits)}")
for r in near_res[:5]:
    print(f"  {r.phrase}  score={r.score:.2f}  freq={r.frequency}")

# Test negation
print()
print("=" * 60)
print("NOT / NOR NEGATION TAGGER")
print("=" * 60)
neg = e.tag_negations(texts)
print(f"  Phrases tagged: {len(neg)}")
for phrase, spans in list(neg.items())[:8]:
    negs = [s for s in spans if s.negated]
    print(f'  "{phrase}" -> {len(spans)} occurrences ({len(negs)} negated)')
    for s in negs[:2]:
        print(f'    negated by "{s.negation_cue}" at doc {s.doc_index} chars [{s.char_start}:{s.char_end}]')

# Test span export
print()
print("=" * 60)
print("PHRASE SPAN EXPORT")
print("=" * 60)
spans = e.extract_phrase_spans(texts)
print(f"  Unique phrases: {len(spans)}, Total spans: {sum(len(v) for v in spans.values())}")
for p, sp_list in list(spans.items())[:5]:
    print(f'  "{p}" -> {len(sp_list)} spans')
    for sp in sp_list[:2]:
        print(f"    doc={sp.doc_index} chars=[{sp.char_start}:{sp.char_end}] tok=[{sp.token_start}:{sp.token_end}]")

print()
print("ALL OPERATORS PASSED")
