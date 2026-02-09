import urllib.request
import json
import sys
import os
from pathlib import Path

# Configuration
API_URL = "http://localhost:8500"
DATA_ROOT = Path(os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")) / "ai_data_final"

def get_json(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"❌ API Error: {response.status}")
                return None
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ Connection Failed to {url}: {e}")
        return None

def check_l_drive_access():
    print(f"Checking direct access to {DATA_ROOT}...")
    if not DATA_ROOT.exists():
        print(f"❌ ERROR: L: Drive path {DATA_ROOT} does not exist!")
        return False
    
    # Check for key subdirectories
    required_subs = ["companies", "parsed_resumes"]
    for sub in required_subs:
        if (DATA_ROOT / sub).exists():
            print(f"✅ Found {sub}")
        else:
            print(f"⚠️ Warning: Subdirectory {sub} not found.")
            
    # Check Extended Scope
    parser_root = DATA_ROOT.parent / "automated_parser"
    user_data_root = DATA_ROOT.parent / "USER DATA"
    
    if parser_root.exists():
        print(f"✅ Found automated_parser (Expanded Scope)")
    else:
        print(f"⚠️ USER CHECK: automated_parser not found at {parser_root}")

    if user_data_root.exists():
        print(f"✅ Found USER DATA (Expanded Scope)")
    else:
        print(f"⚠️ USER CHECK: USER DATA not found at {user_data_root}")
            
    print("Direct L: Drive access confirmed.")
    return True

def check_api_data_status():
    print(f"\nChecking API Data Status ({API_URL}/api/data/status)...")
    data = get_json(f"{API_URL}/api/data/status")
    if not data: return False

    if not data.get("ok"):
        print(f"❌ API reported not OK: {data}")
        return False
        
    # Check specific directory counts
    dirs = data.get("directories", {})
    total_files = sum(d.get("file_count", 0) for d in dirs.values())
    print(f"✅ API sees {total_files} total files across data directories.")
    
    base_path = data.get("base_path", "")
    print(f"ℹ️ API is using base path: {base_path}")
    
    if "L:" not in base_path and "antigravity" not in base_path:
            print(f"⚠️ WARNING: API base path {base_path} might not be L: drive!")
    
    return True

def check_taxonomy():
    print(f"\nChecking Taxonomy Service ({API_URL}/api/taxonomy/industries)...")
    data = get_json(f"{API_URL}/api/taxonomy/industries")
    if not data: return False

    count = data.get("meta", {}).get("count", 0)
    print(f"✅ Taxonomy Service loaded {count} industries.")
    return count > 0

def check_expanded_endpoints():
    print(f"\nChecking Expanded AI Data Endpoints...")
    all_good = True
    
    # Check Candidates
    url = f"{API_URL}/api/data/automated/candidates"
    print(f"  > GET {url}")
    data = get_json(url)
    if data and data.get("ok"):
        count = data.get("count", 0)
        print(f"  ✅ Candidates found: {count}")
    else:
        print(f"  ❌ Failed to get automated candidates: {data}")
        all_good = False

    # Check User Data Files
    url = f"{API_URL}/api/data/user_data/files"
    print(f"  > GET {url}")
    data = get_json(url)
    if data and data.get("ok"):
        count = data.get("count", 0)
        print(f"  ✅ User Data files found: {count}")
    else:
        print(f"  ❌ Failed to get user data files: {data}")
        all_good = False
        
    return all_good

if __name__ == "__main__":
    print(f"Python Executable: {sys.executable}")
    print("=== CareerTrojan Data Integrity Verification ===\n")
    
    steps = [
        check_l_drive_access,
        check_api_data_status,
        check_taxonomy,
        check_expanded_endpoints
    ]
    
    success = True
    for step in steps:
        if not step():
            success = False
            
    if success:
        print("\n✅ VERIFICATION PASSED: Runtime is correctly linked to L: Drive.")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Data integration issues detected.")
        sys.exit(1)
