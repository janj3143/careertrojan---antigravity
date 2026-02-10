"""Quick audit: which React callsites still use old prefixes (not /api/.../v1)?"""
import json, os

data = json.load(open("ENDPOINT_MAPPING_PHASES/Phase15_React_API_Scan_Export/react_api_calls.json", "r", encoding="utf-8"))

old_prefix = []
new_prefix = []
template_urls = []

for c in data["calls"]:
    url = c.get("url", "")
    portal = c.get("portal", "?")
    method = c.get("method", "GET")
    fname = os.path.basename(c.get("file", ""))
    line = c.get("line", 0)
    
    if "${" in url or "`" in url:
        template_urls.append(c)
    elif url.startswith("/api/"):
        new_prefix.append(c)
    else:
        old_prefix.append(c)

print(f"=== REACT API CALLSITE AUDIT ===")
print(f"Total callsites: {len(data['calls'])}")
print(f"Already /api/ prefix: {len(new_prefix)}")
print(f"Template URLs (dynamic): {len(template_urls)}")
print(f"OLD prefix (need update): {len(old_prefix)}")
print()

if old_prefix:
    print("--- NEED UPDATING ---")
    for c in old_prefix:
        url = c.get("url", "")
        portal = c.get("portal", "?")
        method = c.get("method", "GET")
        fname = os.path.basename(c.get("file", ""))
        line = c.get("line", 0)
        print(f"  [{portal:6s}] {method:6s} {url:50s}  {fname}:{line}")

print()
if template_urls:
    print("--- TEMPLATE URLs (check manually) ---")
    for c in template_urls:
        url = c.get("url", "")
        portal = c.get("portal", "?")
        fname = os.path.basename(c.get("file", ""))
        line = c.get("line", 0)
        print(f"  [{portal:6s}] {url:60s}  {fname}:{line}")
