"""Run governance audit against the live CareerTrojan app."""
import os, json
os.environ["TESTING"] = "1"

from services.backend_api.main import app
from services.backend_api.governance.route_governance import run_audit, save_snapshot

# Save baseline snapshot
path = save_snapshot(app)
print(f"Baseline saved: {path}")

# Run full audit
report = run_audit(app, strict=False, include_manifest=False)
d = report.to_dict()
print(f"Total routes: {d['total_routes']}")
print(f"Summary: {json.dumps(d['summary'], indent=2)}")
print()

# Print violations grouped by severity
for sev in ["error", "warning", "info"]:
    viol = [v for v in d["violations"] if v["severity"] == sev]
    if viol:
        print(f"=== {sev.upper()} ({len(viol)}) ===")
        for v in viol:
            print(f"  [{v['rule']}] {v['route_key']} -- {v['message']}")
        print()

# Print drift
if d["drift"]:
    print(f"=== DRIFT ({len(d['drift'])}) ===")
    for dr in d["drift"]:
        print(f"  [{dr['kind']}] {dr['route_key']} -- {dr['detail']}")
