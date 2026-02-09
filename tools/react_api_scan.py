"""
React API Scan Exporter
Scans a React/TS codebase for API calls (fetch/axios) and outputs:
- react_api_calls.json : list of { file, line, method, path }

Usage:
  python tools/react_api_scan.py --root "path/to/react/src" --out "./exports"
"""
import argparse, json, os, re
from datetime import datetime

FETCH_RE = re.compile(r'fetch\(\s*[`"\'](?P<url>[^`"\']+)[`"\']', re.I)
AXIOS_RE = re.compile(r'axios\.(get|post|put|delete|patch)\(\s*[`"\'](?P<url>[^`"\']+)[`"\']', re.I)
METHOD_HINT_RE = re.compile(r'method\s*:\s*[`"\'](?P<m>GET|POST|PUT|DELETE|PATCH)[`"\']', re.I)

def is_code_file(p: str) -> bool:
    return p.endswith((".ts",".tsx",".js",".jsx"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="React src/ root")
    ap.add_argument("--out", required=True, help="Output folder")
    args = ap.parse_args()

    hits = []
    for dirpath, _, files in os.walk(args.root):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if not is_code_file(p):
                continue
            try:
                txt = open(p, "r", encoding="utf-8", errors="ignore").read().splitlines()
            except Exception:
                continue

            for i, line in enumerate(txt, start=1):
                m = FETCH_RE.search(line)
                if m:
                    url = m.group("url")
                    method = "GET"
                    # look ahead a few lines for method hint
                    blob = "\n".join(txt[i:i+6])
                    mh = METHOD_HINT_RE.search(blob)
                    if mh: method = mh.group("m").upper()
                    hits.append({"file": p, "line": i, "method": method, "url": url, "kind": "fetch"})
                m2 = AXIOS_RE.search(line)
                if m2:
                    url = m2.group("url")
                    method = m2.group(1).upper()
                    hits.append({"file": p, "line": i, "method": method, "url": url, "kind": "axios"})

    out = {
        "generated": datetime.utcnow().strftime("%Y-%m-%d"),
        "root": args.root,
        "count": len(hits),
        "calls": hits
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "react_api_calls.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"[OK] Found {len(hits)} callsites -> {args.out}/react_api_calls.json")

if __name__ == "__main__":
    main()
