
# CareerTrojan Runtime Master Verification Logic (Smart Check)
# ==========================================================

import sys
import os
from pathlib import Path
import re
import importlib.util

ROOT = Path("C:/careertrojan")
sys.path.insert(0, str(ROOT))

def check_path(path_str, description, is_dir=False):
    p = ROOT / path_str
    exists = p.exists()
    status = "✅" if exists else "❌"
    print(f"{status} [{description}] {path_str}")
    return exists

def count_endpoints():
    print("\n🔍 Scanning Endpoints...")
    total = 0
    pattern = re.compile(r'@(router|app)\.(get|post|put|delete|patch)')
    
    api_dir = ROOT / "services/backend_api"
    for py_file in api_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            matches = len(pattern.findall(content))
            if matches > 0:
                print(f"   - {py_file.name}: {matches}")
                total += matches
        except Exception:
            pass
            
    print(f"   👉 Total Runtime Endpoints: {total}")
    return total

def verify_imports():
    print("\n🧪 Verifying Critical Imports...")
    modules = [
        "services.backend_api.main",
        "services.backend_api.routers.auth",
        "services.backend_api.services.llm_service"
    ]
    
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"✅ Import OK: {mod}")
        except ImportError as e:
            print(f"❌ Import FAILED: {mod} ({e})")
        except Exception as e:
            print(f"⚠️ Import ERROR: {mod} ({e})")

def main():
    print("=== 🛡? CareerTrojan Smart Verification 🛡? ===\n")
    
    # 1. Structure Check
    print("📂 Checking Directory Structure...")
    check_path("apps/user/index.html", "React User Portal")
    check_path("apps/admin/index.html", "React Admin Portal (Shell)")
    check_path("services/backend_api/main.py", "Backend API Entry")
    check_path("data/user_uploads", "Data Storage")
    
    # 2. Endpoint Count
    count = count_endpoints()
    if count < 50:
        print("\n⚠️ WARNING: Endpoint count seems low. Migration incomplete?")
    else:
        print("\n✅ Endpoint count looks healthy (>50).")

    # 3. Import Check
    verify_imports()

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()
