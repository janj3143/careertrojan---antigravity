"""
CareerTrojan — Evaluation Harness (Model Governance)
=====================================================

Provides systematic testing infrastructure for AI model quality:
  1. Golden Test Sets — curated examples with known correct outputs
  2. Regression Tests — ensure existing behavior is preserved
  3. Metrics Collection — precision, recall, F1, calibration
  4. A/B Comparison — compare model versions side-by-side
  5. Behavioral Tests — check for specific failure modes

Usage:
    from services.ai_engine.evaluation_harness import evaluator
    
    # Run all golden tests
    report = evaluator.run_golden_tests("classification")
    
    # Add a new golden test
    evaluator.add_golden_test(
        category="classification",
        input_data={"text": "Senior Python Developer"},
        expected_output={"industry": "Technology"},
        tolerance=0.1,
    )
    
    # Run regression suite
    report = evaluator.run_regression_suite()

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import hashlib

logger = logging.getLogger("EvaluationHarness")


# ══════════════════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class GoldenTest:
    """A single golden test case with known correct output."""
    test_id: str
    category: str                          # "classification", "extraction", "scoring", etc.
    name: str                              # Human-readable test name
    input_data: Dict[str, Any]             # Input to the model
    expected_output: Any                   # Expected/correct output
    tolerance: float = 0.0                 # Allowed deviation (for numeric outputs)
    tags: List[str] = field(default_factory=list)  # "critical", "edge-case", etc.
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "category": self.category,
            "name": self.name,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "tolerance": self.tolerance,
            "tags": self.tags,
            "created": self.created,
        }


@dataclass
class TestResult:
    """Result of running a single test."""
    test_id: str
    passed: bool
    actual_output: Any
    expected_output: Any
    confidence: float
    latency_ms: float
    error: Optional[str] = None
    deviation: float = 0.0                 # For numeric: |actual - expected|
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "passed": self.passed,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "confidence": round(self.confidence, 4),
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
            "deviation": round(self.deviation, 4),
        }


@dataclass
class EvaluationReport:
    """Aggregate report from running a test suite."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    avg_latency_ms: float
    avg_confidence: float
    
    # Per-category breakdown
    by_category: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Individual results
    results: List[TestResult] = field(default_factory=list)
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "pass_rate": round(self.pass_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "avg_confidence": round(self.avg_confidence, 4),
            "by_category": self.by_category,
            "results": [r.to_dict() for r in self.results],
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
        }


# ══════════════════════════════════════════════════════════════════════════
# Metric Calculators
# ══════════════════════════════════════════════════════════════════════════

class MetricsCalculator:
    """Calculate standard ML metrics from test results."""
    
    @staticmethod
    def precision_recall_f1(
        y_true: List[Any],
        y_pred: List[Any],
        labels: List[Any] = None,
    ) -> Dict[str, float]:
        """Calculate precision, recall, F1 for classification."""
        if not y_true or not y_pred:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        if labels is None:
            labels = list(set(y_true) | set(y_pred))
        
        # Per-label metrics
        metrics = {}
        for label in labels:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics[str(label)] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": sum(1 for t in y_true if t == label),
            }
        
        # Macro-averaged metrics
        avg_precision = sum(m["precision"] for m in metrics.values()) / len(metrics) if metrics else 0.0
        avg_recall = sum(m["recall"] for m in metrics.values()) / len(metrics) if metrics else 0.0
        avg_f1 = sum(m["f1"] for m in metrics.values()) / len(metrics) if metrics else 0.0
        
        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1": avg_f1,
            "per_label": metrics,
        }
    
    @staticmethod
    def calibration_error(
        confidences: List[float],
        correct: List[bool],
        n_bins: int = 10,
    ) -> Dict[str, Any]:
        """Calculate Expected Calibration Error (ECE)."""
        if not confidences or not correct:
            return {"ece": 0.0, "bins": []}
        
        bins = [[] for _ in range(n_bins)]
        
        for conf, is_correct in zip(confidences, correct):
            bin_idx = min(int(conf * n_bins), n_bins - 1)
            bins[bin_idx].append((conf, 1.0 if is_correct else 0.0))
        
        ece = 0.0
        bin_results = []
        
        for i, bin_data in enumerate(bins):
            if bin_data:
                avg_conf = sum(c for c, _ in bin_data) / len(bin_data)
                avg_acc = sum(a for _, a in bin_data) / len(bin_data)
                weight = len(bin_data) / len(confidences)
                ece += weight * abs(avg_acc - avg_conf)
                bin_results.append({
                    "bin": i,
                    "count": len(bin_data),
                    "avg_confidence": avg_conf,
                    "avg_accuracy": avg_acc,
                    "gap": abs(avg_acc - avg_conf),
                })
        
        return {"ece": ece, "bins": bin_results}
    
    @staticmethod
    def regression_metrics(
        y_true: List[float],
        y_pred: List[float],
    ) -> Dict[str, float]:
        """Calculate regression metrics (MAE, RMSE, R²)."""
        if not y_true or not y_pred or len(y_true) != len(y_pred):
            return {"mae": 0.0, "rmse": 0.0, "r2": 0.0}
        
        n = len(y_true)
        
        # MAE
        mae = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / n
        
        # RMSE
        mse = sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / n
        rmse = mse ** 0.5
        
        # R²
        mean_true = sum(y_true) / n
        ss_tot = sum((t - mean_true) ** 2 for t in y_true)
        ss_res = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "mse": mse,
        }


# ══════════════════════════════════════════════════════════════════════════
# Output Comparators
# ══════════════════════════════════════════════════════════════════════════

class OutputComparator:
    """Compare actual vs expected outputs for different types."""
    
    @staticmethod
    def compare(
        actual: Any,
        expected: Any,
        tolerance: float = 0.0,
        compare_type: str = "auto",
    ) -> Tuple[bool, float]:
        """
        Compare actual to expected output.
        
        Returns:
            (passed, deviation)
        """
        if compare_type == "auto":
            compare_type = OutputComparator._infer_type(expected)
        
        if compare_type == "exact":
            return actual == expected, 0.0 if actual == expected else 1.0
        
        elif compare_type == "numeric":
            try:
                actual_num = float(actual) if not isinstance(actual, (int, float)) else actual
                expected_num = float(expected) if not isinstance(expected, (int, float)) else expected
                deviation = abs(actual_num - expected_num)
                passed = deviation <= tolerance
                return passed, deviation
            except (ValueError, TypeError):
                return False, float('inf')
        
        elif compare_type == "contains":
            # Check if expected items are in actual (for lists)
            if isinstance(expected, list) and isinstance(actual, list):
                missing = [e for e in expected if e not in actual]
                deviation = len(missing) / len(expected) if expected else 0.0
                return deviation <= tolerance, deviation
            return False, 1.0
        
        elif compare_type == "dict_subset":
            # Check if expected keys match in actual dict
            if isinstance(expected, dict) and isinstance(actual, dict):
                mismatches = 0
                total = len(expected)
                for k, v in expected.items():
                    if k not in actual:
                        mismatches += 1
                    elif actual[k] != v:
                        mismatches += 0.5  # Partial credit for key present
                deviation = mismatches / total if total > 0 else 0.0
                return deviation <= tolerance, deviation
            return False, 1.0
        
        elif compare_type == "semantic":
            # For text: check similarity (simplified)
            if isinstance(expected, str) and isinstance(actual, str):
                # Jaccard similarity
                actual_words = set(actual.lower().split())
                expected_words = set(expected.lower().split())
                intersection = len(actual_words & expected_words)
                union = len(actual_words | expected_words)
                similarity = intersection / union if union > 0 else 0.0
                return similarity >= (1.0 - tolerance), 1.0 - similarity
            return False, 1.0
        
        else:
            # Default: exact match
            return actual == expected, 0.0 if actual == expected else 1.0
    
    @staticmethod
    def _infer_type(expected: Any) -> str:
        """Infer comparison type from expected value."""
        if isinstance(expected, (int, float)):
            return "numeric"
        elif isinstance(expected, list):
            return "contains"
        elif isinstance(expected, dict):
            return "dict_subset"
        elif isinstance(expected, str) and len(expected) > 50:
            return "semantic"
        else:
            return "exact"


# ══════════════════════════════════════════════════════════════════════════
# Main Evaluation Harness
# ══════════════════════════════════════════════════════════════════════════

class EvaluationHarness:
    """
    Systematic testing infrastructure for AI model quality.
    
    Features:
      - Golden test sets with version control
      - Regression testing with baseline comparison
      - Metrics calculation (precision, recall, calibration)
      - A/B model comparison
      - Behavioral tests for edge cases
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(__file__).parent / "evaluation"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.golden_tests_file = self.storage_dir / "golden_tests.json"
        self.baselines_file = self.storage_dir / "baselines.json"
        self.reports_dir = self.storage_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load existing tests
        self._golden_tests: Dict[str, GoldenTest] = self._load_golden_tests()
        self._baselines: Dict[str, Dict] = self._load_baselines()
        
        # Model executor (injected or default)
        self._executor: Optional[Callable] = None
        self._metrics = MetricsCalculator()
        self._comparator = OutputComparator()
    
    def set_executor(self, executor: Callable[[Dict[str, Any]], Tuple[Any, float]]) -> None:
        """
        Set the model executor function.
        
        Executor signature: (input_data) -> (output, confidence)
        """
        self._executor = executor
    
    def _load_golden_tests(self) -> Dict[str, GoldenTest]:
        """Load golden tests from disk."""
        if self.golden_tests_file.exists():
            try:
                with open(self.golden_tests_file) as f:
                    data = json.load(f)
                return {
                    test_id: GoldenTest(**test_data)
                    for test_id, test_data in data.items()
                }
            except Exception as e:
                logger.warning("Failed to load golden tests: %s", e)
        return {}
    
    def _save_golden_tests(self) -> None:
        """Save golden tests to disk."""
        data = {test_id: test.to_dict() for test_id, test in self._golden_tests.items()}
        with open(self.golden_tests_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_baselines(self) -> Dict[str, Dict]:
        """Load baseline metrics from disk."""
        if self.baselines_file.exists():
            try:
                with open(self.baselines_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load baselines: %s", e)
        return {}
    
    def _save_baselines(self) -> None:
        """Save baselines to disk."""
        with open(self.baselines_file, "w") as f:
            json.dump(self._baselines, f, indent=2)
    
    # ─────────────────────────────────────────────────────────────────────
    # Golden Test Management
    # ─────────────────────────────────────────────────────────────────────
    
    def add_golden_test(
        self,
        category: str,
        name: str,
        input_data: Dict[str, Any],
        expected_output: Any,
        tolerance: float = 0.0,
        tags: List[str] = None,
    ) -> str:
        """Add a new golden test case."""
        # Generate test ID
        test_id = hashlib.sha256(
            json.dumps({"category": category, "input": input_data}, sort_keys=True).encode()
        ).hexdigest()[:12]
        
        test = GoldenTest(
            test_id=test_id,
            category=category,
            name=name,
            input_data=input_data,
            expected_output=expected_output,
            tolerance=tolerance,
            tags=tags or [],
        )
        
        self._golden_tests[test_id] = test
        self._save_golden_tests()
        
        logger.info("Added golden test: %s (%s)", name, test_id)
        return test_id
    
    def remove_golden_test(self, test_id: str) -> bool:
        """Remove a golden test."""
        if test_id in self._golden_tests:
            del self._golden_tests[test_id]
            self._save_golden_tests()
            return True
        return False
    
    def get_golden_tests(
        self,
        category: str = None,
        tags: List[str] = None,
    ) -> List[GoldenTest]:
        """Get golden tests, optionally filtered."""
        tests = list(self._golden_tests.values())
        
        if category:
            tests = [t for t in tests if t.category == category]
        
        if tags:
            tests = [t for t in tests if any(tag in t.tags for tag in tags)]
        
        return tests
    
    # ─────────────────────────────────────────────────────────────────────
    # Test Execution
    # ─────────────────────────────────────────────────────────────────────
    
    def run_golden_tests(
        self,
        category: str = None,
        tags: List[str] = None,
        executor: Callable = None,
    ) -> EvaluationReport:
        """Run golden test suite."""
        start_time = time.time()
        
        executor = executor or self._executor
        if not executor:
            # Try to use AI Gateway as default executor
            try:
                from services.ai_engine.ai_gateway import ai_gateway
                executor = self._make_gateway_executor(ai_gateway)
            except ImportError:
                raise RuntimeError("No executor set and AI Gateway not available")
        
        tests = self.get_golden_tests(category=category, tags=tags)
        
        results: List[TestResult] = []
        by_category: Dict[str, Dict] = {}
        
        for test in tests:
            result = self._run_single_test(test, executor)
            results.append(result)
            
            # Aggregate by category
            if test.category not in by_category:
                by_category[test.category] = {"passed": 0, "failed": 0, "errors": 0}
            
            if result.error:
                by_category[test.category]["errors"] += 1
            elif result.passed:
                by_category[test.category]["passed"] += 1
            else:
                by_category[test.category]["failed"] += 1
        
        # Build report
        passed = sum(1 for r in results if r.passed and not r.error)
        failed = sum(1 for r in results if not r.passed and not r.error)
        errors = sum(1 for r in results if r.error)
        
        report = EvaluationReport(
            suite_name=f"golden_{category or 'all'}",
            total_tests=len(tests),
            passed=passed,
            failed=failed,
            errors=errors,
            pass_rate=passed / len(tests) if tests else 0.0,
            avg_latency_ms=sum(r.latency_ms for r in results) / len(results) if results else 0.0,
            avg_confidence=sum(r.confidence for r in results) / len(results) if results else 0.0,
            by_category=by_category,
            results=results,
            duration_seconds=time.time() - start_time,
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _run_single_test(
        self,
        test: GoldenTest,
        executor: Callable,
    ) -> TestResult:
        """Run a single test case."""
        start_time = time.time()
        
        try:
            output, confidence = executor(test.input_data)
            latency_ms = (time.time() - start_time) * 1000
            
            passed, deviation = self._comparator.compare(
                output,
                test.expected_output,
                tolerance=test.tolerance,
            )
            
            return TestResult(
                test_id=test.test_id,
                passed=passed,
                actual_output=output,
                expected_output=test.expected_output,
                confidence=confidence,
                latency_ms=latency_ms,
                deviation=deviation,
            )
        except Exception as e:
            return TestResult(
                test_id=test.test_id,
                passed=False,
                actual_output=None,
                expected_output=test.expected_output,
                confidence=0.0,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )
    
    def _make_gateway_executor(self, gateway) -> Callable:
        """Create an executor that uses the AI Gateway."""
        def executor(input_data: Dict[str, Any]) -> Tuple[Any, float]:
            # Determine task type from input
            if "prompt" in input_data:
                response = gateway.generate(**input_data)
            elif "resume_text" in input_data:
                response = gateway.score_candidate(**input_data)
            elif "extraction_type" in input_data:
                response = gateway.extract(**input_data)
            elif "category_type" in input_data:
                response = gateway.classify(**input_data)
            else:
                # Default to classify
                response = gateway.classify(text=str(input_data))
            
            return response.result, response.calibrated_confidence
        
        return executor
    
    # ─────────────────────────────────────────────────────────────────────
    # Regression Testing
    # ─────────────────────────────────────────────────────────────────────
    
    def set_baseline(self, suite_name: str, report: EvaluationReport) -> None:
        """Set baseline metrics for regression comparison."""
        self._baselines[suite_name] = {
            "timestamp": datetime.now().isoformat(),
            "pass_rate": report.pass_rate,
            "avg_latency_ms": report.avg_latency_ms,
            "avg_confidence": report.avg_confidence,
            "by_category": report.by_category,
        }
        self._save_baselines()
        logger.info("Set baseline for suite: %s (pass_rate=%.2f%%)", suite_name, report.pass_rate * 100)
    
    def compare_to_baseline(
        self,
        report: EvaluationReport,
        fail_on_regression: bool = False,
    ) -> Dict[str, Any]:
        """Compare current report to baseline."""
        baseline = self._baselines.get(report.suite_name)
        
        if not baseline:
            return {"status": "no_baseline", "message": "No baseline set for this suite"}
        
        comparison = {
            "status": "compared",
            "baseline_timestamp": baseline["timestamp"],
            "pass_rate_delta": report.pass_rate - baseline["pass_rate"],
            "latency_delta_ms": report.avg_latency_ms - baseline["avg_latency_ms"],
            "confidence_delta": report.avg_confidence - baseline["avg_confidence"],
            "regressions": [],
            "improvements": [],
        }
        
        # Check for regressions
        if report.pass_rate < baseline["pass_rate"] - 0.01:  # 1% tolerance
            comparison["regressions"].append({
                "metric": "pass_rate",
                "baseline": baseline["pass_rate"],
                "current": report.pass_rate,
                "delta": report.pass_rate - baseline["pass_rate"],
            })
        
        if report.avg_latency_ms > baseline["avg_latency_ms"] * 1.2:  # 20% tolerance
            comparison["regressions"].append({
                "metric": "latency",
                "baseline": baseline["avg_latency_ms"],
                "current": report.avg_latency_ms,
                "delta_pct": (report.avg_latency_ms / baseline["avg_latency_ms"] - 1) * 100,
            })
        
        # Check for improvements
        if report.pass_rate > baseline["pass_rate"] + 0.01:
            comparison["improvements"].append({
                "metric": "pass_rate",
                "baseline": baseline["pass_rate"],
                "current": report.pass_rate,
                "delta": report.pass_rate - baseline["pass_rate"],
            })
        
        comparison["regression_detected"] = len(comparison["regressions"]) > 0
        
        if fail_on_regression and comparison["regression_detected"]:
            raise AssertionError(f"Regression detected: {comparison['regressions']}")
        
        return comparison
    
    def run_regression_suite(
        self,
        executor: Callable = None,
        fail_on_regression: bool = False,
    ) -> Tuple[EvaluationReport, Dict[str, Any]]:
        """Run all golden tests and compare to baseline."""
        report = self.run_golden_tests(executor=executor)
        comparison = self.compare_to_baseline(report, fail_on_regression=fail_on_regression)
        return report, comparison
    
    # ─────────────────────────────────────────────────────────────────────
    # Behavioral Tests
    # ─────────────────────────────────────────────────────────────────────
    
    def run_behavioral_tests(
        self,
        test_cases: List[Dict[str, Any]],
        executor: Callable = None,
    ) -> Dict[str, Any]:
        """
        Run behavioral tests for specific failure modes.
        
        Example test_cases:
          [
            {"name": "empty_input", "input": {"text": ""}, "expect_error": False},
            {"name": "very_long_input", "input": {"text": "x" * 10000}, "expect_error": False},
            {"name": "special_chars", "input": {"text": "<script>alert('xss')</script>"}, "expect_error": False},
          ]
        """
        executor = executor or self._executor
        if not executor:
            try:
                from services.ai_engine.ai_gateway import ai_gateway
                executor = self._make_gateway_executor(ai_gateway)
            except ImportError:
                raise RuntimeError("No executor available")
        
        results = []
        for test in test_cases:
            start = time.time()
            try:
                output, confidence = executor(test["input"])
                error = None
                got_error = False
            except Exception as e:
                output = None
                confidence = 0.0
                error = str(e)
                got_error = True
            
            expect_error = test.get("expect_error", False)
            passed = (got_error == expect_error)
            
            results.append({
                "name": test["name"],
                "passed": passed,
                "expected_error": expect_error,
                "got_error": got_error,
                "error": error,
                "output": output,
                "latency_ms": (time.time() - start) * 1000,
            })
        
        return {
            "total": len(test_cases),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "results": results,
        }
    
    # ─────────────────────────────────────────────────────────────────────
    # A/B Comparison
    # ─────────────────────────────────────────────────────────────────────
    
    def compare_models(
        self,
        executor_a: Callable,
        executor_b: Callable,
        tests: List[GoldenTest] = None,
    ) -> Dict[str, Any]:
        """Compare two model versions side by side."""
        tests = tests or list(self._golden_tests.values())
        
        results_a = []
        results_b = []
        
        for test in tests:
            result_a = self._run_single_test(test, executor_a)
            result_b = self._run_single_test(test, executor_b)
            results_a.append(result_a)
            results_b.append(result_b)
        
        pass_rate_a = sum(1 for r in results_a if r.passed) / len(results_a) if results_a else 0.0
        pass_rate_b = sum(1 for r in results_b if r.passed) / len(results_b) if results_b else 0.0
        
        avg_latency_a = sum(r.latency_ms for r in results_a) / len(results_a) if results_a else 0.0
        avg_latency_b = sum(r.latency_ms for r in results_b) / len(results_b) if results_b else 0.0
        
        # Find disagreements
        disagreements = []
        for i, test in enumerate(tests):
            if results_a[i].actual_output != results_b[i].actual_output:
                disagreements.append({
                    "test_id": test.test_id,
                    "test_name": test.name,
                    "output_a": results_a[i].actual_output,
                    "output_b": results_b[i].actual_output,
                    "expected": test.expected_output,
                    "a_correct": results_a[i].passed,
                    "b_correct": results_b[i].passed,
                })
        
        return {
            "model_a": {
                "pass_rate": pass_rate_a,
                "avg_latency_ms": avg_latency_a,
            },
            "model_b": {
                "pass_rate": pass_rate_b,
                "avg_latency_ms": avg_latency_b,
            },
            "winner": "a" if pass_rate_a > pass_rate_b else "b" if pass_rate_b > pass_rate_a else "tie",
            "pass_rate_delta": pass_rate_b - pass_rate_a,
            "latency_delta_ms": avg_latency_b - avg_latency_a,
            "disagreements": disagreements,
            "agreement_rate": 1.0 - len(disagreements) / len(tests) if tests else 1.0,
        }
    
    # ─────────────────────────────────────────────────────────────────────
    # Reports
    # ─────────────────────────────────────────────────────────────────────
    
    def _save_report(self, report: EvaluationReport) -> Path:
        """Save report to disk."""
        filename = f"{report.suite_name}_{report.timestamp.replace(':', '-')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info("Saved report to %s", filepath)
        return filepath
    
    def get_recent_reports(
        self,
        suite_name: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent evaluation reports."""
        reports = []
        
        for filepath in sorted(self.reports_dir.glob("*.json"), reverse=True):
            if limit and len(reports) >= limit:
                break
            
            try:
                with open(filepath) as f:
                    report = json.load(f)
                
                if suite_name and report.get("suite_name") != suite_name:
                    continue
                
                reports.append(report)
            except Exception:
                continue
        
        return reports


# ══════════════════════════════════════════════════════════════════════════
# Seed Golden Tests (industry-specific)
# ══════════════════════════════════════════════════════════════════════════

def seed_golden_tests(harness: EvaluationHarness) -> int:
    """Seed the harness with initial golden tests."""
    tests_added = 0
    
    # Classification tests
    classification_tests = [
        {
            "name": "Software Engineer classification",
            "input": {"text": "Senior Software Engineer with 10 years Python experience, AWS certified"},
            "expected": {"industry": "Technology"},
            "category": "classification",
        },
        {
            "name": "Nurse classification",
            "input": {"text": "Registered Nurse with ICU experience, BLS certified"},
            "expected": {"industry": "Healthcare"},
            "category": "classification",
        },
        {
            "name": "Financial Analyst classification",
            "input": {"text": "CFA Level III, 5 years in equity research at Goldman Sachs"},
            "expected": {"industry": "Finance"},
            "category": "classification",
        },
        {
            "name": "Marketing Manager classification",
            "input": {"text": "Digital Marketing Manager, expertise in SEO, Google Ads, HubSpot"},
            "expected": {"industry": "Marketing"},
            "category": "classification",
        },
    ]
    
    # Extraction tests
    extraction_tests = [
        {
            "name": "Email extraction",
            "input": {"text": "Contact me at john.smith@example.com", "extraction_type": "contact"},
            "expected": {"emails": ["john.smith@example.com"]},
            "category": "extraction",
            "tolerance": 0.0,
        },
        {
            "name": "Phone extraction",
            "input": {"text": "Call 555-123-4567 or 555.987.6543", "extraction_type": "contact"},
            "expected": {"phones": ["555-123-4567", "555.987.6543"]},
            "category": "extraction",
            "tolerance": 0.0,
        },
    ]
    
    # Scoring tests (numeric, with tolerance)
    scoring_tests = [
        {
            "name": "Senior engineer high score",
            "input": {
                "resume_text": "10 years software engineering, Python, AWS, led teams of 20+ engineers",
                "skills": ["Python", "AWS", "Leadership", "Architecture"],
                "experience_years": 10,
            },
            "expected": 75.0,  # Expected score
            "category": "scoring",
            "tolerance": 15.0,  # +/- 15 points
        },
        {
            "name": "Entry level lower score",
            "input": {
                "resume_text": "Recent graduate, internship at startup, knows Python basics",
                "skills": ["Python"],
                "experience_years": 1,
            },
            "expected": 40.0,
            "category": "scoring",
            "tolerance": 20.0,
        },
    ]
    
    all_tests = classification_tests + extraction_tests + scoring_tests
    
    for test_config in all_tests:
        try:
            harness.add_golden_test(
                category=test_config["category"],
                name=test_config["name"],
                input_data=test_config["input"],
                expected_output=test_config["expected"],
                tolerance=test_config.get("tolerance", 0.1),
                tags=["seed", test_config["category"]],
            )
            tests_added += 1
        except Exception as e:
            logger.warning("Failed to add test '%s': %s", test_config["name"], e)
    
    return tests_added


# ══════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ══════════════════════════════════════════════════════════════════════════

evaluator = EvaluationHarness()


# ══════════════════════════════════════════════════════════════════════════
# CLI / Demo
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("═" * 70)
    print("CareerTrojan Evaluation Harness — Model Quality Testing")
    print("═" * 70)
    
    # Seed tests if none exist
    if not evaluator._golden_tests:
        print("\n📝 Seeding golden tests...")
        count = seed_golden_tests(evaluator)
        print(f"   Added {count} golden tests")
    
    print(f"\n📊 Loaded {len(evaluator._golden_tests)} golden tests")
    
    # List categories
    categories = set(t.category for t in evaluator._golden_tests.values())
    print(f"   Categories: {', '.join(categories)}")
    
    # Run tests if gateway available
    try:
        print("\n🔍 Running golden tests...")
        report = evaluator.run_golden_tests()
        
        print(f"\n📈 Results:")
        print(f"   Total: {report.total_tests}")
        print(f"   Passed: {report.passed}")
        print(f"   Failed: {report.failed}")
        print(f"   Errors: {report.errors}")
        print(f"   Pass Rate: {report.pass_rate * 100:.1f}%")
        print(f"   Avg Latency: {report.avg_latency_ms:.1f}ms")
        print(f"   Avg Confidence: {report.avg_confidence:.2f}")
        
        # Set baseline
        print("\n✅ Setting baseline for regression tests...")
        evaluator.set_baseline(report.suite_name, report)
        
    except Exception as e:
        print(f"\n⚠️  Could not run tests: {e}")
        print("   (AI Gateway not available - tests will run when gateway is ready)")
    
    print("\n✅ Evaluation Harness ready")
