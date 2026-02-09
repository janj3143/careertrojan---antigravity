import os
import stat
import time

# Security Policy Configuration
REQUIRE_ADMIN_2FA = True
ENFORCE_READONLY_LOGS = True

class SecurityPolicyViolation(Exception):
    pass

def verify_admin_access(user_role: str, two_factor_token: str = None) -> bool:
    """
    Verifies if an Admin can access the system.
    Strict enforcement of 2FA for 'admin' role.
    """
    if user_role != 'admin':
        return True # Non-admins don't need this specific 2FA check for general access, but Access Control will block them from Admin areas.
    
    if REQUIRE_ADMIN_2FA:
        if not two_factor_token:
            raise SecurityPolicyViolation("SECURITY_ALERT: Admin access attempted without 2FA Token.")
        
        # STUB: In production, verify against TOTP provider (e.g. Google Authenticator / Authy)
        # For Phase 1 validation: Token must be present and 'valid' string
        if two_factor_token != "valid-token-123":
             raise SecurityPolicyViolation("SECURITY_ALERT: Invalid 2FA Token provided.")
             
        print(f"[SECURITY] Admin 2FA Verified for session.")
        return True
    return True

def enforce_log_immutability(log_file_path: str):
    """
    Sets a file to Read-Only mode to prevent tampering.
    To be called immediately after a log rotation or write session closes.
    """
    if not ENFORCE_READONLY_LOGS:
        return

    if not os.path.exists(log_file_path):
        print(f"[WARN] Log file not found: {log_file_path}")
        return

    try:
        # Remove Write permissions (User/Group/Others)
        # Windows: os.chmod with existing permissions masked logic or stat.S_IREAD
        os.chmod(log_file_path, stat.S_IREAD)
        print(f"[SECURITY] Log Immutability Enforced: {log_file_path} is now READ-ONLY.")
    except Exception as e:
        print(f"[CRITICAL] Failed to set Read-Only on log: {e}")
        # In a real secure runtime, we might halt here.

def mock_masquerade_access(admin_user: str, target_user: str):
    """
    Logs the 'Masquerade' event to a secure audit log before granting the token.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    audit_entry = f"[{timestamp}] ALERT: Admin '{admin_user}' initiated MASQUERADE session for Target '{target_user}'"
    
    # This specific log should definitely be immutable
    print(audit_entry)
    # In production: write to C:\careertrojan\logs\audit_security.log
