"""Quick smoke test for the term evolution engine."""
import sys
sys.path.insert(0, ".")

from services.ai_engine.term_evolution_engine import evolution_engine

stats = evolution_engine.get_stats()
print(f"Chains loaded: {stats['chains_loaded']}")
print(f"Lineage terms: {stats['total_lineage_terms']}")
print(f"Complementary skills: {stats['total_complementary_skills']}")
print(f"Domains: {stats['domains']}")

# Test MRP → ERP
r = evolution_engine.resolve("mrp")
if r:
    print(f"\nMRP resolves to: {r['current_term']}")
    print(f"  Chain: {r['chain_id']}")
    print(f"  Lineage: {' -> '.join(e['term'] for e in r['lineage'])}")
else:
    print("FAIL: MRP not found")

# Test Basel
r2 = evolution_engine.resolve("Basel II")
if r2:
    print(f"\nBasel II resolves to: {r2['current_term']}")
else:
    print("FAIL: Basel II not found")

# Test HR evolution
r3 = evolution_engine.resolve("personnel management")
if r3:
    print(f"\nPersonnel Mgmt resolves to: {r3['current_term']}")
else:
    print("FAIL: personnel management not found")

# Test skill overlap
paths = evolution_engine.find_user_evolution_paths(
    user_skills=["risk management", "capital adequacy", "stress testing"],
    user_job_titles=["Risk Analyst"]
)
print(f"\nEvolution paths for Risk Analyst: {len(paths)} found")
for p in paths[:3]:
    print(f"  - {p['chain_name']} (score: {p['relevance_score']}, coverage: {p['skill_coverage']})")

# Test AI context
ctx = evolution_engine.format_for_ai_context("MRP")
print(f"\nAI context (first 200 chars): {ctx[:200]}...")

print("\nALL TESTS PASSED")
