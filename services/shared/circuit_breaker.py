"""
Circuit Breaker — CaReerTroJan
================================
Thread-safe circuit breaker with three states:

    CLOSED  →  (failures >= threshold)  →  OPEN
    OPEN    →  (timeout expires)        →  HALF_OPEN
    HALF_OPEN → (success)               →  CLOSED
    HALF_OPEN → (failure)               →  OPEN

Usage:
    from services.shared.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker("openai", failure_threshold=5, recovery_timeout=60)
    if not cb.allow_request():
        return fallback_response()
    try:
        result = call_provider()
        cb.record_success()
        return result
    except Exception:
        cb.record_failure()
        raise

Or as a decorator:
    @cb.protect
    def call_provider():
        ...

Author: CaReerTroJan System
Date: February 26, 2026
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and the request is rejected."""
    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit '{name}' is OPEN — retry after {retry_after:.1f}s")


@dataclass
class CircuitStats:
    """Snapshot of circuit breaker metrics."""
    name: str
    state: str
    failure_count: int
    success_count: int
    total_calls: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    time_in_current_state: float


class CircuitBreaker:
    """
    Thread-safe circuit breaker for external service calls.

    Args:
        name: Identifier (e.g. "openai", "anthropic")
        failure_threshold: Number of consecutive failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait in OPEN state before allowing a probe (default: 60)
        half_open_max_calls: Max concurrent calls allowed in HALF_OPEN state (default: 1)
        success_threshold: Successes required in HALF_OPEN to close circuit (default: 2)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0           # successes in HALF_OPEN
        self._total_calls = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._state_changed_at = time.monotonic()
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition()
            return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        with self._lock:
            self._maybe_transition()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False  # already probing

            # OPEN
            return False

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._total_calls += 1
            self._last_success_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info("Circuit '%s' CLOSED (recovered after %d successes)", self.name, self._success_count)
            elif self._state == CircuitState.CLOSED:
                # Reset failure streak on success
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._total_calls += 1
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed — back to OPEN
                self._transition_to(CircuitState.OPEN)
                logger.warning("Circuit '%s' re-OPENED (probe failed)", self.name)

            elif self._state == CircuitState.CLOSED and self._failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    "Circuit '%s' OPENED after %d consecutive failures",
                    self.name, self._failure_count,
                )

    def get_stats(self) -> CircuitStats:
        """Get current circuit breaker stats."""
        with self._lock:
            self._maybe_transition()
            return CircuitStats(
                name=self.name,
                state=self._state.value,
                failure_count=self._failure_count,
                success_count=self._success_count,
                total_calls=self._total_calls,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                time_in_current_state=time.monotonic() - self._state_changed_at,
            )

    def reset(self) -> None:
        """Force-reset the circuit to CLOSED."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            logger.info("Circuit '%s' force-RESET to CLOSED", self.name)

    def _maybe_transition(self) -> None:
        """Auto-transition OPEN → HALF_OPEN after recovery_timeout (called under lock)."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._state_changed_at
            if elapsed >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info("Circuit '%s' → HALF_OPEN (recovery timeout elapsed)", self.name)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state (called under lock)."""
        self._state = new_state
        self._state_changed_at = time.monotonic()
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            self._half_open_calls = 0

    def protect(self, func: Callable) -> Callable:
        """
        Decorator that wraps a function with circuit breaker protection.
        Raises CircuitOpenError if the circuit is open.
        """
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                retry_after = self.recovery_timeout - (time.monotonic() - self._state_changed_at)
                raise CircuitOpenError(self.name, max(0, retry_after))
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception:
                self.record_failure()
                raise
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


# ══════════════════════════════════════════════════════════════
# Registry — one breaker per provider
# ══════════════════════════════════════════════════════════════

class CircuitBreakerRegistry:
    """
    Singleton registry of circuit breakers keyed by service name.

    Usage:
        registry = get_circuit_registry()
        cb = registry.get("openai")  # auto-creates if missing
        stats = registry.all_stats()
    """

    def __init__(
        self,
        default_threshold: int = 5,
        default_timeout: float = 60.0,
    ):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        self.default_threshold = default_threshold
        self.default_timeout = default_timeout

    def get(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker by name."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=kwargs.get("failure_threshold", self.default_threshold),
                    recovery_timeout=kwargs.get("recovery_timeout", self.default_timeout),
                    half_open_max_calls=kwargs.get("half_open_max_calls", 1),
                    success_threshold=kwargs.get("success_threshold", 2),
                )
            return self._breakers[name]

    def all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all registered circuit breakers."""
        with self._lock:
            return {name: cb.get_stats().__dict__ for name, cb in self._breakers.items()}

    def reset_all(self) -> None:
        """Force-reset all breakers to CLOSED."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()


# Module-level singleton
_registry: Optional[CircuitBreakerRegistry] = None
_registry_lock = threading.Lock()


def get_circuit_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry singleton."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = CircuitBreakerRegistry(
                    default_threshold=int(__import__("os").getenv("CB_FAILURE_THRESHOLD", "5")),
                    default_timeout=float(__import__("os").getenv("CB_RECOVERY_TIMEOUT", "60")),
                )
    return _registry
