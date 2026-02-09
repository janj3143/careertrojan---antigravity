import sys
import os
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
# Add project root to sys.path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

try:
    # Runtime Import: careertrojan.services.backend_api.main
    from services.backend_api.main import app
    print("SUCCESS: Imported backend_api app")
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"CRITICAL ERROR: Could not import app: {e}")
    sys.exit(1)

# Override Auth for testing
try:
    from services.backend_api.app.deps import require_user
    app.dependency_overrides[require_user] = lambda: {"sub": "1", "role": "user", "email": "test@example.com"}
    print("SUCCESS: Overrode require_user auth dependency")
except ImportError:
    print("WARNING: Could not import require_user to override auth")

# client = TestClient(app)  <-- Removed global instantiation

def run_smoke_tests():
    print("\n" + "="*50)
    print("      INTELLICV PLATFORM SMOKE TEST      ")
    print("="*50 + "\n")
    
    # Use context manager to trigger lifespan (startup/shutdown) events
    with TestClient(app) as client:
        test_resume_parsing(client)
        test_coaching_questions(client)
        test_coaching_review(client)
        test_resume_enrichment(client)
        test_mentorship_flow(client)
    
    print("\n" + "="*50)
    print("           ALL TESTS COMPLETED           ")
    print("="*50 + "\n")

def test_resume_parsing(client):
    print(">>> Testing Resume Parsing (/api/resume/parse)...")
    
    # Create dummy resume
    dummy_path = Path("smoke_test_resume.txt")
    dummy_path.write_text("Smoke test resume for Jane Doe. experience: 10 years Python. Email: jane@test.com", encoding="utf-8")
    
    try:
        with open(dummy_path, "rb") as f:
            response = client.post(
                "/api/resume/parse", 
                files={"file": ("smoke_test_resume.txt", f, "text/plain")}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("  [PASS] Status 200 OK")
                print(f"  [INFO] Extracted Email: {data['data']['parsed_data'].get('emails')}")
                assert "jane@test.com" in data['data']['parsed_data']['emails'][0]
            else:
                print(f"  [FAIL] Status {response.status_code}")
                # print(f"  [INFO] Response: {response.text}")

    finally:
        if dummy_path.exists():
            dummy_path.unlink()

def test_coaching_questions(client):
    print("\n>>> Testing Coaching Questions (/api/coaching/questions)...")
    payload = {
        "question_type": "Technical",
        "count": 2,
        "resume": {"raw_text": "Senior Python Developer with AWS experience."}
    }
    
    response = client.post("/api/coaching/questions", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("  [PASS] Status 200 OK")
        print(f"  [INFO] Questions: {data[:2]}")
        assert len(data) > 0
    else:
        print(f"  [FAIL] Status {response.status_code}")
        print(f"  [INFO] Response: {response.text}")

def test_coaching_review(client):
    print("\n>>> Testing Answer Review (/api/coaching/practice/review)...")
    payload = {
        "question": "Explain dependency injection",
        "answer": "It is a design pattern...",
        "job_context": "Software Engineer"
    }
    
    response = client.post("/api/coaching/practice/review", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("  [PASS] Status 200 OK")
        print(f"  [INFO] Feedback Summary: {data.get('summary')}")
    else:
        print(f"  [FAIL] Status {response.status_code}")
        print(f"  [INFO] Response: {response.text}")

def test_resume_enrichment(client):
    print("\n>>> Testing Resume Enrichment (/api/resume/enrich)...")
    # Using existing functionality from ResumeStore in same process
    # Note: This relies on previous parse having succeeded and stored a resume
    response = client.post("/api/resume/enrich")
    if response.status_code == 200:
        data = response.json()
        print("  [PASS] Status 200 OK")
        print(f"  [INFO] Keywords: {len(data['data']['enrichment'].get('keywords', []))}")
        print(f"  [INFO] Skills Detected: {data['data']['enrichment'].get('skills_detected', [])}")
    else:
        print(f"  [FAIL] Status {response.status_code}")
        # print(f"  [INFO] Response: {response.text}")

def test_mentorship_flow(client):
    print("\n>>> Testing Mentorship Flow (/api/mentorship)...")
    
    # 1. Create Link
    payload = {
        "user_id": "1",
        "mentor_id": "mentor_007",
        "program_id": "prog_1"
    }
    response = client.post("/api/mentorship/links", json=payload)
    
    if response.status_code == 201:
        data = response.json()
        link_id = data['link_id']
        print(f"  [PASS] Created Link: {link_id}")
        
        # 2. Create Note
        note_payload = {
            "link_id": link_id,
            "mentor_id": "mentor_007",
            "note_content": "Smoke test note",
            "note_type": "session"
        }
        resp2 = client.post("/api/mentorship/notes", json=note_payload)
        if resp2.status_code == 201:
             print(f"  [PASS] Created Note: {resp2.json().get('note_id')}")
        else:
             print(f"  [FAIL] Note Creation Failed: {resp2.status_code}")
    else:
        print(f"  [FAIL] Link Creation Failed: {response.status_code}")
        print(f"  [INFO] Error: {response.text}")

if __name__ == "__main__":
    run_smoke_tests()
