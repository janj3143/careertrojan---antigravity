import os
import json
import sys
from pathlib import Path

# Configuration
RUNTIME_ROOT = os.environ.get("CAREERTROJAN_RUNTIME_ROOT", r"C:\careertrojan")
USER_DATA_ROOT = os.path.join(RUNTIME_ROOT, "user_data")
AI_DATA_ROOT_WIN = r"L:\antigravity_version_ai_data_final"
AI_DATA_ROOT_LINUX = "/mnt/l/antigravity_version_ai_data_final" # Hypothetical mount

def print_pass(msg):
    print(f"[\033[92mPASS\033[0m] {msg}")

def print_fail(msg):
    print(f"[\033[91mFAIL\033[0m] {msg}")

def print_warn(msg):
    print(f"[\033[93mWARN\033[0m] {msg}")

def check_environment_paths():
    print("\n--- 1. Environment Path Validation ---")
    
    # Platform Check
    is_windows = sys.platform == "win32"
    print(f"Detected Platform: {sys.platform}")

    # Check Runtime Root
    if os.path.exists(RUNTIME_ROOT):
        print_pass(f"Runtime Root found: {RUNTIME_ROOT}")
    else:
        print_fail(f"Runtime Root NOT found: {RUNTIME_ROOT}")

    # Check Data Root (Platform Aware)
    target_data_root = AI_DATA_ROOT_WIN if is_windows else AI_DATA_ROOT_LINUX
    
    # Note: On the agent we might not have the L: drive, so we check if strict mode is off
    if os.path.exists(target_data_root):
        print_pass(f"AI Data Root found: {target_data_root}")
    else:
        print_warn(f"AI Data Root not found at {target_data_root}. (Expected if running outside of dedicated runtime VM)")

def verify_test_user_seeding():
    print("\n--- 2. Test User Verification ---")
    users_file = os.path.join(USER_DATA_ROOT, "users.json")
    
    if not os.path.exists(users_file):
        print_fail(f"User database file not found: {users_file}")
        print("    -> Has 'bootstrap.ps1' been run?")
        return

    try:
        with open(users_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        # Handle if it's a single object or list (bootstrap creates a single object currently)
        user = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
        
        if user and user.get("username") == "janj3143":
            print_pass(f"Test user 'janj3143' found.")
            print(f"    Role: {user.get('role')}")
            print(f"    Status: {user.get('status')}")
        else:
            print_fail("Test user 'janj3143' not found in users.json.")
            
    except Exception as e:
        print_fail(f"Failed to read users.json: {e}")

def simulate_docker_services():
    print("\n--- 3. Service Definition Check ---")
    docker_compose = os.path.join(RUNTIME_ROOT, "infra", "docker", "compose.yaml")
    
    if os.path.exists(docker_compose):
        print_pass(f"Docker Compose definition found: {docker_compose}")
        # In a real smoke test, we might run `docker ps` here
    else:
        # Fallback check
        alt_compose = os.path.join(RUNTIME_ROOT, "infra", "docker", "docker-compose.yml")
        if os.path.exists(alt_compose):
            print_pass(f"Docker Compose definition found: {alt_compose}")
        else:
            print_warn(f"Docker Compose file missing. Checked 'compose.yaml' and 'docker-compose.yml'")

def check_frontend_components():
    print("\n--- 4. Frontend Critical Components (Graphics/Visuals) ---")
    
    # Define critical components to check (relative to RUNTIME_ROOT)
    components = [
        r"apps\user-portal\src\components\visuals\ChartContainer.tsx",
        r"apps\user-portal\src\components\pages\umarketu\components\FitAnalysis.tsx",
        r"apps\user-portal\src\components\pages\umarketu\components\ResumeTuning.tsx",
        r"apps\user-portal\src\components\pages\umarketu\services\creditService.ts"
    ]
    
    all_found = True
    for partial_path in components:
        full_path = os.path.join(RUNTIME_ROOT, partial_path)
        if os.path.exists(full_path):
            print_pass(f"Component found: {os.path.basename(full_path)}")
        else:
            print_fail(f"Component MISSING: {partial_path}")
            all_found = False
            
    if all_found:
        print_pass("All critical visual components are present.")
    else:
        print_fail("Some visual components are missing. Graphics validation failed.")

if __name__ == "__main__":
    print(f"CareerTrojan Runtime Smoke Test v1.0")
    print("======================================")
    
    check_environment_paths()
    verify_test_user_seeding()
    simulate_docker_services()
    check_frontend_components()
    
    print("\nSmoke Test Complete.")
