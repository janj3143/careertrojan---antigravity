import sys
import os

# Ensure we can import the shared security module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'shared'))

try:
    import security_policy
except ImportError:
    # Fallback for manual run location
    sys.path.append(os.path.join("C:\\careertrojan", "services", "shared"))
    import security_policy

def run_test():
    print("--- CareerTrojan Admin Security Stub Test ---")
    
    # 1. Test 2FA Enforcement
    print("\n[TEST 1] Testing Admin Access WITHOUT 2FA...")
    try:
        security_policy.verify_admin_access(user_role="admin", two_factor_token=None)
        print("FAIL: Admin allowed without 2FA!")
    except security_policy.SecurityPolicyViolation as e:
        print(f"PASS: Blocked as expected: {e}")

    print("\n[TEST 2] Testing Admin Access WITH Valid 2FA...")
    try:
        security_policy.verify_admin_access(user_role="admin", two_factor_token="valid-token-123")
        print("PASS: Admin access granted.")
    except Exception as e:
        print(f"FAIL: Error: {e}")

    # 2. Test Log Immutability
    print("\n[TEST 3] Testing Log Immutability...")
    test_log = "C:\\careertrojan\\logs\\test_security_event.log"
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(test_log), exist_ok=True)
    
    # Write "Log"
    with open(test_log, "w") as f:
        f.write("Sensitive Admin Action Logged.\n")
    
    # Enforce Read-Only
    security_policy.enforce_log_immutability(test_log)
    
    # Try to Overwrite (Should Fail/Except)
    try:
        with open(test_log, "a") as f:
            f.write("Malicious Edit Attempt.\n")
        print("FAIL: Was able to write to 'Read-Only' log!")
    except PermissionError:
        print("PASS: PermissionError caught. Log is immutable.")
    except Exception as e:
        print(f"PASS: Write blocked ({type(e).__name__}).")

    # Cleanup (Reset permissions to delete)
    import stat
    os.chmod(test_log, stat.S_IWRITE)
    os.remove(test_log)
    print("\n--- Security Stub Verification Complete ---")

if __name__ == "__main__":
    run_test()
