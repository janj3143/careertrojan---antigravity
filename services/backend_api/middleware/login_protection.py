"""
Login Brute-Force Protection
==============================

Tracks failed login attempts per IP address using an in-memory
sliding-window.  After ``MAX_FAILED_ATTEMPTS`` failures within
``LOCKOUT_WINDOW_SECONDS``, further login attempts from that IP
are rejected with HTTP 429 for ``LOCKOUT_DURATION_SECONDS``.

Env overrides:
    LOGIN_MAX_FAILED_ATTEMPTS  (default: 5)
    LOGIN_LOCKOUT_WINDOW       (default: 300  — 5 min)
    LOGIN_LOCKOUT_DURATION     (default: 900  — 15 min)
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger("login_protection")

MAX_FAILED_ATTEMPTS = int(os.getenv("LOGIN_MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_WINDOW = int(os.getenv("LOGIN_LOCKOUT_WINDOW", "300"))
LOCKOUT_DURATION = int(os.getenv("LOGIN_LOCKOUT_DURATION", "900"))


class LoginProtection:
    """Per-IP failed-login tracker with automatic lockout."""

    def __init__(
        self,
        max_attempts: int = MAX_FAILED_ATTEMPTS,
        window_seconds: int = LOCKOUT_WINDOW,
        lockout_seconds: int = LOCKOUT_DURATION,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        # ip → list of failure timestamps
        self._failures: Dict[str, List[float]] = defaultdict(list)
        # ip → lockout expiry timestamp
        self._lockouts: Dict[str, float] = {}

    def _prune(self, ip: str, now: float):
        cutoff = now - self.window_seconds
        self._failures[ip] = [t for t in self._failures[ip] if t > cutoff]

    def is_locked_out(self, ip: str) -> tuple[bool, Optional[int]]:
        """
        Check if an IP is currently locked out.
        Returns (locked: bool, retry_after_seconds: int | None).
        """
        now = time.time()

        # Check active lockout
        if ip in self._lockouts:
            expiry = self._lockouts[ip]
            if now < expiry:
                retry_after = int(expiry - now) + 1
                return True, retry_after
            else:
                # Lockout expired — clear
                del self._lockouts[ip]
                self._failures.pop(ip, None)

        return False, None

    def record_failure(self, ip: str):
        """Record a failed login attempt. May trigger lockout."""
        now = time.time()
        self._prune(ip, now)
        self._failures[ip].append(now)

        if len(self._failures[ip]) >= self.max_attempts:
            self._lockouts[ip] = now + self.lockout_seconds
            logger.warning(
                "IP %s locked out for %ds after %d failed login attempts",
                ip, self.lockout_seconds, len(self._failures[ip]),
            )

    def record_success(self, ip: str):
        """Clear failure history on successful login."""
        self._failures.pop(ip, None)
        self._lockouts.pop(ip, None)

    def reset(self):
        """Clear all state (useful for testing)."""
        self._failures.clear()
        self._lockouts.clear()


# Singleton instance — import and use across the app
login_protection = LoginProtection()
