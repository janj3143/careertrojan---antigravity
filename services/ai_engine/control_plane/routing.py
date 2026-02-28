"""
CareerTrojan — Routing Policy Engine
=====================================

Intelligent model/engine selection based on task type and context.

Routing Strategies:
    - all_engines: Run all available engines (default for scoring)
    - fast_path: Use only lightweight engines (for real-time)
    - llm_direct: Route directly to LLM (for generation tasks)
    - collocation_first: Use collocation engine + fallback (for extraction)
    - expert_only: Use only expert system (for rule-based queries)
    - hybrid: Combine ML + LLM + rules (for complex queries)

Policy Rules:
    - If uncertainty high → use more engines or deterministic pipeline
    - If extraction → smaller model + rules (fast, consistent)
    - If rewrite/style → LLM (creative, context-aware)
    - If compliance risk → constrained prompts + validators
    - If latency critical → fast_path only

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("RoutingPolicy")


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    strategy: str
    engines: List[str]
    reason: str
    confidence: float = 1.0
    fallback_strategy: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "engines": self.engines,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "fallback_strategy": self.fallback_strategy,
            "constraints": self.constraints,
        }


class RoutingPolicy:
    """
    Policy engine for intelligent AI request routing.
    
    Decides which engines/models to use based on:
        - Task type (score, extract, match, rewrite, qa, chart, questions)
        - Context (text length, user role, latency requirements)
        - Historical performance (which engines work best for similar requests)
        - Cost considerations
    """
    
    # Default strategies per task type
    DEFAULT_STRATEGIES = {
        "score": "all_engines",
        "extract": "collocation_first",
        "match": "hybrid",
        "rewrite": "llm_direct",
        "qa": "llm_direct",
        "chart": "fast_path",
        "questions": "hybrid",
    }
    
    # Engine sets for each strategy
    STRATEGY_ENGINES = {
        "all_engines": ["bayesian", "neural", "nlp", "fuzzy", "statistical", "expert_system"],
        "fast_path": ["bayesian", "expert_system"],
        "llm_direct": ["llm"],
        "collocation_first": ["collocation", "expert_system"],
        "expert_only": ["expert_system"],
        "hybrid": ["collocation", "expert_system", "llm"],
        "ml_only": ["bayesian", "neural", "nlp"],
    }
    
    # Latency budgets (ms)
    LATENCY_BUDGETS = {
        "realtime": 100,      # <100ms (autocomplete, live typing)
        "interactive": 500,   # <500ms (button clicks)
        "background": 5000,   # <5s (batch processing)
        "async": 30000,       # <30s (complex analysis)
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "routing_config.json"
        self._lock = Lock()
        
        # Load custom rules if available
        self.custom_rules: List[Dict[str, Any]] = []
        self._load_config()
        
        # Performance tracking
        self._engine_latencies: Dict[str, List[float]] = {}
        self._engine_success_rates: Dict[str, float] = {}
        
        logger.info("RoutingPolicy initialized (%d custom rules)", len(self.custom_rules))
    
    def _load_config(self):
        """Load routing configuration from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                self.custom_rules = config.get("custom_rules", [])
                
                # Override defaults if specified
                if "default_strategies" in config:
                    self.DEFAULT_STRATEGIES.update(config["default_strategies"])
                if "strategy_engines" in config:
                    self.STRATEGY_ENGINES.update(config["strategy_engines"])
                    
            except Exception as e:
                logger.warning("Failed to load routing config: %s", e)
    
    def _save_config(self):
        """Save current configuration to disk."""
        try:
            config = {
                "default_strategies": self.DEFAULT_STRATEGIES,
                "strategy_engines": self.STRATEGY_ENGINES,
                "custom_rules": self.custom_rules,
                "updated": datetime.now().isoformat(),
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save routing config: %s", e)
    
    def decide(
        self,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        latency_class: str = "interactive",
        user_role: str = "user",
    ) -> str:
        """
        Decide which routing strategy to use.
        
        Args:
            task_type: The type of AI task (score, extract, match, etc.)
            context: Additional context (text_length, experience_years, etc.)
            latency_class: Latency requirement (realtime, interactive, background, async)
            user_role: User role (user, admin, mentor)
        
        Returns:
            Strategy name (e.g., "all_engines", "fast_path", "llm_direct")
        """
        context = context or {}
        
        # Check custom rules first
        for rule in self.custom_rules:
            if self._matches_rule(rule, task_type, context, latency_class, user_role):
                logger.debug("Matched custom rule: %s", rule.get("name", "unnamed"))
                return rule.get("strategy", self.DEFAULT_STRATEGIES.get(task_type, "all_engines"))
        
        # Apply latency constraints
        budget_ms = self.LATENCY_BUDGETS.get(latency_class, 500)
        
        if budget_ms <= 100:
            # Realtime: only fastest engines
            if task_type in ("score", "extract", "match"):
                return "fast_path"
            elif task_type in ("chart",):
                return "expert_only"
            # LLM tasks can't be realtime
            return "expert_only"
        
        if budget_ms <= 500:
            # Interactive: avoid slow engines
            if task_type == "score":
                return "ml_only"  # Skip neural if slow
            return self.DEFAULT_STRATEGIES.get(task_type, "all_engines")
        
        # Background/Async: full power
        return self.DEFAULT_STRATEGIES.get(task_type, "all_engines")
    
    def decide_full(
        self,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        latency_class: str = "interactive",
        user_role: str = "user",
    ) -> RoutingDecision:
        """
        Get full routing decision with engines and constraints.
        
        Returns a RoutingDecision with complete details.
        """
        context = context or {}
        strategy = self.decide(task_type, context, latency_class, user_role)
        
        engines = self.STRATEGY_ENGINES.get(strategy, ["expert_system"])
        
        # Build reason
        reason_parts = [f"Task: {task_type}", f"Latency: {latency_class}"]
        if user_role != "user":
            reason_parts.append(f"Role: {user_role}")
        
        # Determine constraints
        constraints = {}
        
        if strategy == "llm_direct":
            # LLM-specific constraints
            text_length = context.get("text_length", 0)
            if text_length > 10000:
                constraints["max_tokens"] = 2000
                constraints["truncate_input"] = True
            
            # Compliance constraints for certain roles
            if user_role == "admin":
                constraints["allow_pii"] = True
            else:
                constraints["allow_pii"] = False
        
        if latency_class == "realtime":
            constraints["timeout_ms"] = 100
            constraints["skip_slow_engines"] = True
        
        # Determine fallback
        fallback = None
        if strategy == "all_engines":
            fallback = "fast_path"
        elif strategy == "llm_direct":
            fallback = "collocation_first"
        
        return RoutingDecision(
            strategy=strategy,
            engines=engines,
            reason=" | ".join(reason_parts),
            confidence=0.9,
            fallback_strategy=fallback,
            constraints=constraints,
        )
    
    def _matches_rule(
        self,
        rule: Dict[str, Any],
        task_type: str,
        context: Dict[str, Any],
        latency_class: str,
        user_role: str,
    ) -> bool:
        """Check if a context matches a custom rule."""
        conditions = rule.get("conditions", {})
        
        # Check task_type
        if "task_type" in conditions:
            if conditions["task_type"] != task_type:
                return False
        
        # Check latency_class
        if "latency_class" in conditions:
            if conditions["latency_class"] != latency_class:
                return False
        
        # Check user_role
        if "user_role" in conditions:
            if conditions["user_role"] != user_role:
                return False
        
        # Check context conditions
        for key, expected in conditions.get("context", {}).items():
            actual = context.get(key)
            
            if isinstance(expected, dict):
                # Range check
                if "min" in expected and (actual is None or actual < expected["min"]):
                    return False
                if "max" in expected and (actual is None or actual > expected["max"]):
                    return False
            elif actual != expected:
                return False
        
        return True
    
    def add_custom_rule(
        self,
        name: str,
        strategy: str,
        conditions: Dict[str, Any],
        priority: int = 0,
    ) -> bool:
        """
        Add a custom routing rule.
        
        Args:
            name: Rule name for debugging
            strategy: Strategy to use when matched
            conditions: Matching conditions
            priority: Higher priority rules are checked first
        
        Returns:
            True if added successfully
        """
        rule = {
            "name": name,
            "strategy": strategy,
            "conditions": conditions,
            "priority": priority,
            "created": datetime.now().isoformat(),
        }
        
        with self._lock:
            self.custom_rules.append(rule)
            # Sort by priority (descending)
            self.custom_rules.sort(key=lambda r: r.get("priority", 0), reverse=True)
        
        self._save_config()
        logger.info("Added custom rule: %s", name)
        return True
    
    def remove_custom_rule(self, name: str) -> bool:
        """Remove a custom rule by name."""
        with self._lock:
            original_len = len(self.custom_rules)
            self.custom_rules = [r for r in self.custom_rules if r.get("name") != name]
            removed = len(self.custom_rules) < original_len
        
        if removed:
            self._save_config()
            logger.info("Removed custom rule: %s", name)
        return removed
    
    def record_engine_performance(
        self,
        engine: str,
        latency_ms: float,
        success: bool,
    ):
        """Record engine performance for adaptive routing."""
        with self._lock:
            if engine not in self._engine_latencies:
                self._engine_latencies[engine] = []
            
            self._engine_latencies[engine].append(latency_ms)
            # Keep only recent 100 samples
            if len(self._engine_latencies[engine]) > 100:
                self._engine_latencies[engine] = self._engine_latencies[engine][-100:]
            
            # Update success rate (exponential moving average)
            alpha = 0.1
            current_rate = self._engine_success_rates.get(engine, 0.8)
            self._engine_success_rates[engine] = alpha * (1.0 if success else 0.0) + (1 - alpha) * current_rate
    
    def get_recommended_engines(
        self,
        strategy: str,
        budget_ms: float = 500,
    ) -> List[str]:
        """
        Get recommended engines based on strategy and performance data.
        
        Filters out engines that are too slow or have poor success rates.
        """
        base_engines = self.STRATEGY_ENGINES.get(strategy, ["expert_system"])
        
        recommended = []
        for engine in base_engines:
            # Check latency
            latencies = self._engine_latencies.get(engine, [])
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                if avg_latency > budget_ms * 0.8:  # 80% of budget
                    logger.debug("Skipping %s: avg latency %.1fms > budget %.1fms", 
                               engine, avg_latency, budget_ms * 0.8)
                    continue
            
            # Check success rate
            success_rate = self._engine_success_rates.get(engine, 0.8)
            if success_rate < 0.5:
                logger.debug("Skipping %s: success rate %.2f < 0.5", engine, success_rate)
                continue
            
            recommended.append(engine)
        
        # Always have at least one engine
        if not recommended:
            recommended = ["expert_system"]
        
        return recommended
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        with self._lock:
            avg_latencies = {}
            for engine, latencies in self._engine_latencies.items():
                if latencies:
                    avg_latencies[engine] = round(sum(latencies) / len(latencies), 2)
            
            return {
                "custom_rules": len(self.custom_rules),
                "strategies": list(self.STRATEGY_ENGINES.keys()),
                "default_strategies": dict(self.DEFAULT_STRATEGIES),
                "engine_latencies_ms": avg_latencies,
                "engine_success_rates": {k: round(v, 3) for k, v in self._engine_success_rates.items()},
            }
    
    def explain_decision(
        self,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        latency_class: str = "interactive",
        user_role: str = "user",
    ) -> str:
        """
        Get a human-readable explanation of a routing decision.
        
        Useful for debugging and admin visibility.
        """
        decision = self.decide_full(task_type, context, latency_class, user_role)
        
        lines = [
            f"Routing Decision for task '{task_type}':",
            f"  Strategy: {decision.strategy}",
            f"  Engines: {', '.join(decision.engines)}",
            f"  Reason: {decision.reason}",
        ]
        
        if decision.constraints:
            lines.append(f"  Constraints: {json.dumps(decision.constraints)}")
        
        if decision.fallback_strategy:
            lines.append(f"  Fallback: {decision.fallback_strategy}")
        
        return "\n".join(lines)


# ── Module-level Singleton ───────────────────────────────────────────────

_router_instance: Optional[RoutingPolicy] = None
_router_lock = Lock()


def get_router() -> RoutingPolicy:
    """Get the module-level RoutingPolicy singleton."""
    global _router_instance
    
    with _router_lock:
        if _router_instance is None:
            _router_instance = RoutingPolicy()
        return _router_instance
