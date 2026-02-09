"""
Join Endpoint Graph
Inputs:
- endpoints_from_fastapi.json (Phase14 output)
- react_api_calls.json        (Phase15 output)
- optional visual_registry.json (your registry listing visuals->endpoints)

Outputs:
- endpoints.json
- connections.json
Which drive your Phase13 visual map + endpoint table.

Usage:
  python tools/join_endpoint_graph.py --fastapi ./exports/endpoints_from_fastapi.json --react ./exports/react_api_calls.json --out ./joined
"""
import argparse, json, os, re
from datetime import datetime

def norm(u: str) -> str:
    # normalize URL to a path when possible
    if u.startswith("http"):
        # strip scheme/host
        m = re.match(r"https?://[^/]+(?P<p>/.*)$", u)
        if m: return m.group("p")
    return u

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fastapi", required=True)
    ap.add_argument("--react", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--registry", required=False, help="optional visual registry json")
    args = ap.parse_args()

    fa = json.load(open(args.fastapi, "r", encoding="utf-8"))
    rc = json.load(open(args.react, "r", encoding="utf-8"))

    fastapi_eps = {(e["method"], e["path"]): e for e in fa.get("endpoints", [])}
    callsites = rc.get("calls", [])

    # Build endpoints list enriched with consumers from React
    consumers_by_key = {}
    for c in callsites:
        path = norm(c.get("url", ""))
        method = c.get("method", "GET").upper()
        key = (method, path)
        consumers_by_key.setdefault(key, set()).add(f'react:{os.path.basename(c.get("file",""))}:{c.get("line",0)}')

    endpoints_out = []
    nodes = []
    edges = []

    # base nodes: portals/services (you can expand this later)
    nodes.extend([
        {"id":"user_portal","type":"portal","label":"User Portal (React)"},
        {"id":"admin_portal","type":"portal","label":"Admin Portal (React)"},
        {"id":"mentor_portal","type":"portal","label":"Mentor Portal (React)"},
        {"id":"backend_api","type":"service","label":"FastAPI Backend"}
    ])

    # create endpoint entries from fastapi, attach consumers if any
    for (method, path), meta in sorted(fastapi_eps.items(), key=lambda x: (x[0][1], x[0][0])):
        eid = f'{meta.get("name","endpoint")}.{method.lower()}.{abs(hash(path))%10**8}'
        consumers = sorted(list(consumers_by_key.get((method, path), set())))
        endpoints_out.append({
            "id": eid,
            "method": method,
            "path": "/api"+path if path.startswith("/") and not path.startswith("/api") else path,
            "service": "backend_api",
            "category": (meta.get("tags") or ["misc"])[0],
            "auth": "user",          # you can refine via tag conventions
            "token_cost": 0,         # you can join to billing policy later
            "description": "",
            "params": [],
            "produces": [],
            "consumed_by": consumers,
            "notes": "auto-generated from introspection + react scan"
        })
        nodes.append({"id": eid, "type":"endpoint", "label": f"{method} {path}"})
        edges.append({"from":"backend_api","to":eid,"label":"exposes"})
        if consumers:
            edges.append({"from":"user_portal","to":"backend_api","label":"calls"})

    # Optional registry join: visuals->endpoints becomes additional consumers
    if args.registry and os.path.exists(args.registry):
        reg = json.load(open(args.registry,"r",encoding="utf-8"))
        # expected: [{visual_id, endpoints:[{method,path}]}]
        # you can adapt this to your registry schema
        pass

    out_endpoints = {"generated": datetime.utcnow().strftime("%Y-%m-%d"), "endpoints": endpoints_out}
    out_graph = {"nodes": nodes, "edges": edges}

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "endpoints.json"), "w", encoding="utf-8") as f:
        json.dump(out_endpoints, f, indent=2)
    with open(os.path.join(args.out, "connections.json"), "w", encoding="utf-8") as f:
        json.dump(out_graph, f, indent=2)

    print(f"[OK] Wrote {len(endpoints_out)} endpoints + {len(nodes)} nodes + {len(edges)} edges -> {args.out}")

if __name__ == "__main__":
    main()
