"""
Unit tests — Login Brute-Force Protection
==========================================

Tests the per-IP sliding-window lockout system that protects the
/login endpoint from credential-stuffing attacks.

Covers:
  - Single failure tracking
  - Lockout trigger after N failures
  - Lockout expiry (time-based)
  - Successful login clears history
  - Independent IP tracking
  - Reset method
"""

import time
import pytest

# ---------------------------------------------------------------------------
# We import the CLASS directly so we can instantiate with custom thresholds
# for fast, deterministic tests (no sleeps).
# ---------------------------------------------------------------------------
from services.backend_api.middleware.login_protection import LoginProtection


@pytest.mark.unit
class TestLoginProtectionFailureTracking:
    """Verify that failures are recorded and counted correctly."""

    def test_no_lockout_on_first_attempt(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked

    def test_single_failure_does_not_lockout(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked

    def test_four_failures_below_threshold(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        for _ in range(4):
            lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked

    def test_five_failures_triggers_lockout(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        for _ in range(5):
            lp.record_failure("10.0.0.1")
        locked, retry_after = lp.is_locked_out("10.0.0.1")
        assert locked
        assert retry_after is not None
        assert retry_after > 0

    def test_six_failures_still_locked(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        for _ in range(6):
            lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert locked


@pytest.mark.unit
class TestLoginProtectionLockoutExpiry:
    """Verify that lockouts expire after the configured duration."""

    def test_lockout_expires_after_duration(self):
        lp = LoginProtection(max_attempts=2, window_seconds=300, lockout_seconds=1)
        lp.record_failure("10.0.0.1")
        lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert locked

        # Wait for lockout to expire
        time.sleep(1.5)
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked

    def test_retry_after_decreases_over_time(self):
        lp = LoginProtection(max_attempts=2, window_seconds=300, lockout_seconds=5)
        lp.record_failure("10.0.0.1")
        lp.record_failure("10.0.0.1")

        _, retry_1 = lp.is_locked_out("10.0.0.1")
        time.sleep(0.5)
        _, retry_2 = lp.is_locked_out("10.0.0.1")
        # retry_after should decrease (or stay same at int resolution)
        assert retry_2 <= retry_1


@pytest.mark.unit
class TestLoginProtectionSuccessReset:
    """Verify that a successful login clears failure history."""

    def test_success_clears_failures(self):
        lp = LoginProtection(max_attempts=5, window_seconds=300, lockout_seconds=60)
        for _ in range(4):
            lp.record_failure("10.0.0.1")
        lp.record_success("10.0.0.1")
        # One more failure should NOT trigger lockout (counter was reset)
        lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked

    def test_success_clears_active_lockout(self):
        lp = LoginProtection(max_attempts=2, window_seconds=300, lockout_seconds=60)
        lp.record_failure("10.0.0.1")
        lp.record_failure("10.0.0.1")
        assert lp.is_locked_out("10.0.0.1")[0]

        lp.record_success("10.0.0.1")
        assert not lp.is_locked_out("10.0.0.1")[0]


@pytest.mark.unit
class TestLoginProtectionIPIsolation:
    """Verify that tracking is per-IP — one IP's failures don't affect another."""

    def test_different_ips_independent(self):
        lp = LoginProtection(max_attempts=3, window_seconds=300, lockout_seconds=60)
        for _ in range(3):
            lp.record_failure("10.0.0.1")
        # IP .1 is locked
        assert lp.is_locked_out("10.0.0.1")[0]
        # IP .2 is NOT locked
        assert not lp.is_locked_out("10.0.0.2")[0]

    def test_success_on_one_ip_doesnt_clear_another(self):
        lp = LoginProtection(max_attempts=3, window_seconds=300, lockout_seconds=60)
        for _ in range(3):
            lp.record_failure("10.0.0.1")
            lp.record_failure("10.0.0.2")
        lp.record_success("10.0.0.1")
        assert not lp.is_locked_out("10.0.0.1")[0]
        assert lp.is_locked_out("10.0.0.2")[0]


@pytest.mark.unit
class TestLoginProtectionWindowPruning:
    """Verify that old failures outside the window are pruned."""

    def test_old_failures_pruned(self):
        lp = LoginProtection(max_attempts=3, window_seconds=1, lockout_seconds=60)
        lp.record_failure("10.0.0.1")
        lp.record_failure("10.0.0.1")
        # Wait for window to expire
        time.sleep(1.5)
        # This is only the 1st failure in the new window
        lp.record_failure("10.0.0.1")
        locked, _ = lp.is_locked_out("10.0.0.1")
        assert not locked


@pytest.mark.unit
class TestLoginProtectionReset:
    """Verify the reset() method clears all state."""

    def test_reset_clears_everything(self):
        lp = LoginProtection(max_attempts=2, window_seconds=300, lockout_seconds=60)
        lp.record_failure("10.0.0.1")
        lp.record_failure("10.0.0.1")
        assert lp.is_locked_out("10.0.0.1")[0]

        lp.reset()
        assert not lp.is_locked_out("10.0.0.1")[0]
