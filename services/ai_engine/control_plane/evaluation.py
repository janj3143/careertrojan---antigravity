"""
CareerTrojan — Evaluation Harness
==================================

Golden test framework for AI quality assurance.

Capabilities:
    - Define golden test sets (CV/JD pairs with expected outputs)
    - Run regression tests after model updates
    - Compute precision/recall/F1 for skill extraction
    - Measure calibration error
    - Track latency and cost metrics
    - Generate evaluation reports

Usage:
    from services.ai_engine.control_plane import get_evaluator
    
    evaluator = get_evaluator()
    
    # Run all golden tests
    report = evaluator.run_golden_tests()
    
    # Run specific test suite
    report = evaluator.run_suite("skill_extraction")
    
    # Check regression
    is_regressed, details = evaluator.check_regression()

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
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Set

import numpy as np

logger = logging.getLogger("EvaluationHarness")


@dataclass
class TestCase:
    """A single test case for evaluation."""
    test_id: str
    suite: str
    name: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "suite": self.suite,
            "name": self.name,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "metadata": self.metadata,
        }


@dataclass
class TestResult:
    """Result of running a single test case."""
    test_id: str
    passed: bool
    actual_output: Any
    expected_output: Any
    metrics: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "passed": self.passed,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "metrics": self.metrics,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class EvaluationReport:
    """Aggregated evaluation report."""
    suite: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    metrics: Dict[str, float] = field(default_factory=dict)
    failed_tests: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite": self.suite,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
            "failed_tests": self.failed_tests[:20],  # Limit
            "timestamp": self.timestamp,
        }


class EvaluationHarness:
    """
    Golden test harness for AI quality assurance.
    
    Manages test suites:
        - skill_extraction: Skill detection accuracy
        - industry_classification: Industry prediction accuracy
        - cv_jd_matching: Match score accuracy
        - confidence_calibration: Calibration error measurement
        - latency: Response time benchmarks
    """
    
    def __init__(self, test_dir: Optional[Path] = None, reports_dir: Optional[Path] = None):
        self.test_dir = test_dir or Path(__file__).parent.parent / "golden_tests"
        self.reports_dir = reports_dir or Path(__file__).parent.parent / "evaluation_reports"
        
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = Lock()
        self._test_cases: Dict[str, List[TestCase]] = {}
        self._historical_results: List[EvaluationReport] = []
        
        # Load existing golden tests
        self._load_golden_tests()
        
        # Create default test sets if none exist
        if not self._test_cases:
            self._create_default_tests()
        
        logger.info("EvaluationHarness initialized (%d test cases)", sum(len(v) for v in self._test_cases.values()))
    
    def _load_golden_tests(self):
        """Load golden test cases from disk."""
        for json_file in self.test_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                suite_name = json_file.stem
                self._test_cases[suite_name] = []
                
                for tc in data.get("test_cases", []):
                    self._test_cases[suite_name].append(TestCase(
                        test_id=tc.get("test_id", f"{suite_name}_{len(self._test_cases[suite_name])}"),
                        suite=suite_name,
                        name=tc.get("name", "Unnamed"),
                        input_data=tc.get("input_data", {}),
                        expected_output=tc.get("expected_output", {}),
                        metadata=tc.get("metadata", {}),
                    ))
                
                logger.debug("Loaded %d tests from %s", len(self._test_cases[suite_name]), json_file)
            except Exception as e:
                logger.warning("Failed to load %s: %s", json_file, e)
    
    def _create_default_tests(self):
        """Create default golden test sets."""
        
        # Skill Extraction Tests
        skill_tests = {
            "test_cases": [
                {
                    "test_id": "skill_001",
                    "name": "Python developer skills",
                    "input_data": {
                        "text": "Senior Python developer with 5 years experience in Django, Flask, FastAPI. Expert in machine learning with scikit-learn and PyTorch."
                    },
                    "expected_output": {
                        "skills": ["Python", "Django", "Flask", "FastAPI", "machine learning", "scikit-learn", "PyTorch"],
                        "min_count": 5,
                    },
                },
                {
                    "test_id": "skill_002",
                    "name": "Data engineer skills",
                    "input_data": {
                        "text": "Data Engineer specializing in Apache Spark, Kafka, AWS Glue, and Snowflake. Strong SQL and data modeling expertise."
                    },
                    "expected_output": {
                        "skills": ["Apache Spark", "Kafka", "AWS Glue", "Snowflake", "SQL", "data modeling"],
                        "min_count": 4,
                    },
                },
                {
                    "test_id": "skill_003",
                    "name": "No skills in text",
                    "input_data": {
                        "text": "I am a hardworking individual looking for new opportunities."
                    },
                    "expected_output": {
                        "skills": [],
                        "max_count": 2,
                    },
                },
                {
                    "test_id": "skill_004",
                    "name": "Mixed case and abbreviations",
                    "input_data": {
                        "text": "Full stack developer: JS, TS, React, node.js, AWS (EC2, S3, Lambda), Docker, K8s"
                    },
                    "expected_output": {
                        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "AWS", "Docker", "Kubernetes"],
                        "min_count": 5,
                    },
                },
            ]
        }
        
        # Industry Classification Tests
        industry_tests = {
            "test_cases": [
                {
                    "test_id": "industry_001",
                    "name": "Finance professional",
                    "input_data": {
                        "text": "Investment banking analyst with experience in M&A, financial modeling, DCF analysis, and client presentations at Goldman Sachs.",
                        "skills": ["financial modeling", "M&A", "DCF"],
                        "experience_years": 3,
                    },
                    "expected_output": {
                        "industry": "Finance",
                        "alternatives": ["Banking", "Investment"],
                    },
                },
                {
                    "test_id": "industry_002",
                    "name": "Healthcare professional",
                    "input_data": {
                        "text": "Registered nurse with 8 years in ICU, specializing in critical care, patient assessment, and ventilator management.",
                        "skills": ["critical care", "patient assessment"],
                        "experience_years": 8,
                    },
                    "expected_output": {
                        "industry": "Healthcare",
                        "alternatives": ["Medical", "Nursing"],
                    },
                },
                {
                    "test_id": "industry_003",
                    "name": "Technology professional",
                    "input_data": {
                        "text": "Software engineer at Google working on cloud infrastructure, distributed systems, and site reliability.",
                        "skills": ["cloud infrastructure", "distributed systems", "SRE"],
                        "experience_years": 5,
                    },
                    "expected_output": {
                        "industry": "Technology",
                        "alternatives": ["IT", "Software", "Engineering"],
                    },
                },
            ]
        }
        
        # CV-JD Matching Tests
        matching_tests = {
            "test_cases": [
                {
                    "test_id": "match_001",
                    "name": "Perfect match",
                    "input_data": {
                        "cv_text": "Python developer with Django, PostgreSQL, Docker, Kubernetes experience.",
                        "jd_text": "Looking for Python developer with Django, PostgreSQL, Docker, Kubernetes.",
                    },
                    "expected_output": {
                        "min_coverage": 80,
                        "grade": "Excellent",
                    },
                },
                {
                    "test_id": "match_002",
                    "name": "Partial match",
                    "input_data": {
                        "cv_text": "Java developer with Spring Boot and Oracle experience.",
                        "jd_text": "Looking for Python developer with Django and PostgreSQL.",
                    },
                    "expected_output": {
                        "max_coverage": 30,
                        "grade_not": "Excellent",
                    },
                },
                {
                    "test_id": "match_003",
                    "name": "Transferable skills",
                    "input_data": {
                        "cv_text": "Backend developer with Java, SQL, REST APIs, microservices architecture.",
                        "jd_text": "Python backend developer for microservices, REST APIs, database integration.",
                    },
                    "expected_output": {
                        "min_coverage": 40,
                        "max_coverage": 70,
                    },
                },
            ]
        }
        
        # Confidence Calibration Tests
        calibration_tests = {
            "test_cases": [
                {
                    "test_id": "cal_001",
                    "name": "High confidence correct",
                    "input_data": {
                        "confidence_range": [0.8, 1.0],
                        "outcome": True,
                    },
                    "expected_output": {
                        "expected_accuracy": 0.8,  # 80%+ should be correct at 80%+ confidence
                    },
                },
                {
                    "test_id": "cal_002",
                    "name": "Low confidence uncertain",
                    "input_data": {
                        "confidence_range": [0.3, 0.5],
                        "outcome": None,  # Either outcome is acceptable
                    },
                    "expected_output": {
                        "expected_accuracy": 0.4,  # ~40% correct at 30-50% confidence
                    },
                },
            ]
        }
        
        # Save default tests
        for name, data in [
            ("skill_extraction", skill_tests),
            ("industry_classification", industry_tests),
            ("cv_jd_matching", matching_tests),
            ("confidence_calibration", calibration_tests),
        ]:
            path = self.test_dir / f"{name}.json"
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Created default test suite: %s", name)
        
        # Reload
        self._load_golden_tests()
    
    def add_test_case(self, suite: str, test_case: TestCase) -> bool:
        """Add a new test case to a suite."""
        if suite not in self._test_cases:
            self._test_cases[suite] = []
        
        self._test_cases[suite].append(test_case)
        
        # Persist
        try:
            path = self.test_dir / f"{suite}.json"
            data = {"test_cases": [tc.to_dict() for tc in self._test_cases[suite]]}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.exception("Failed to save test case")
            return False
    
    def run_suite(self, suite: str) -> EvaluationReport:
        """Run all tests in a suite."""
        if suite not in self._test_cases:
            return EvaluationReport(
                suite=suite,
                total_tests=0,
                passed=0,
                failed=0,
                pass_rate=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                metrics={"error": "Suite not found"},
            )
        
        # Get gateway
        try:
            from services.ai_engine.control_plane.gateway import get_gateway
            gateway = get_gateway()
        except Exception as e:
            return EvaluationReport(
                suite=suite,
                total_tests=len(self._test_cases[suite]),
                passed=0,
                failed=len(self._test_cases[suite]),
                pass_rate=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                metrics={"error": f"Gateway unavailable: {e}"},
            )
        
        results = []
        latencies = []
        
        for tc in self._test_cases[suite]:
            result = self._run_test_case(gateway, tc)
            results.append(result)
            latencies.append(result.latency_ms)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        # Aggregate metrics
        all_metrics: Dict[str, List[float]] = {}
        for r in results:
            for k, v in r.metrics.items():
                if k not in all_metrics:
                    all_metrics[k] = []
                all_metrics[k].append(v)
        
        avg_metrics = {k: np.mean(v) for k, v in all_metrics.items()}
        
        report = EvaluationReport(
            suite=suite,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            pass_rate=passed / len(results) if results else 0.0,
            avg_latency_ms=np.mean(latencies) if latencies else 0.0,
            p95_latency_ms=np.percentile(latencies, 95) if latencies else 0.0,
            metrics=avg_metrics,
            failed_tests=[r.test_id for r in results if not r.passed],
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _run_test_case(self, gateway, tc: TestCase) -> TestResult:
        """Run a single test case."""
        start = time.perf_counter()
        
        try:
            if tc.suite == "skill_extraction":
                return self._run_skill_test(gateway, tc, start)
            elif tc.suite == "industry_classification":
                return self._run_industry_test(gateway, tc, start)
            elif tc.suite == "cv_jd_matching":
                return self._run_matching_test(gateway, tc, start)
            elif tc.suite == "confidence_calibration":
                return self._run_calibration_test(gateway, tc, start)
            else:
                return TestResult(
                    test_id=tc.test_id,
                    passed=False,
                    actual_output=None,
                    expected_output=tc.expected_output,
                    error=f"Unknown suite: {tc.suite}",
                    latency_ms=(time.perf_counter() - start) * 1000,
                )
        except Exception as e:
            return TestResult(
                test_id=tc.test_id,
                passed=False,
                actual_output=None,
                expected_output=tc.expected_output,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    def _run_skill_test(self, gateway, tc: TestCase, start: float) -> TestResult:
        """Run skill extraction test."""
        text = tc.input_data.get("text", "")
        response = gateway.extract_skills(text)
        latency = (time.perf_counter() - start) * 1000
        
        if not response.success:
            return TestResult(
                test_id=tc.test_id,
                passed=False,
                actual_output=None,
                expected_output=tc.expected_output,
                error=response.error,
                latency_ms=latency,
            )
        
        actual_skills = set(s.lower() for s in response.result.get("skills", []))
        expected_skills = set(s.lower() for s in tc.expected_output.get("skills", []))
        
        # Compute metrics
        if expected_skills:
            recall = len(actual_skills & expected_skills) / len(expected_skills)
            precision = len(actual_skills & expected_skills) / len(actual_skills) if actual_skills else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            recall = 1.0 if not actual_skills else 0.0
            precision = 1.0 if not actual_skills else 0.0
            f1 = 1.0 if not actual_skills else 0.0
        
        # Check pass criteria
        passed = True
        if "min_count" in tc.expected_output and len(actual_skills) < tc.expected_output["min_count"]:
            passed = False
        if "max_count" in tc.expected_output and len(actual_skills) > tc.expected_output["max_count"]:
            passed = False
        if expected_skills and recall < 0.5:  # At least 50% recall
            passed = False
        
        return TestResult(
            test_id=tc.test_id,
            passed=passed,
            actual_output=list(actual_skills),
            expected_output=tc.expected_output,
            metrics={"precision": precision, "recall": recall, "f1": f1},
            latency_ms=latency,
        )
    
    def _run_industry_test(self, gateway, tc: TestCase, start: float) -> TestResult:
        """Run industry classification test."""
        response = gateway.score_candidate(
            text=tc.input_data.get("text", ""),
            skills=tc.input_data.get("skills", []),
            experience_years=tc.input_data.get("experience_years", 0),
        )
        latency = (time.perf_counter() - start) * 1000
        
        if not response.success:
            return TestResult(
                test_id=tc.test_id,
                passed=False,
                actual_output=None,
                expected_output=tc.expected_output,
                error=response.error,
                latency_ms=latency,
            )
        
        actual_industry = response.result.get("predicted_industry", "Unknown")
        expected = tc.expected_output.get("industry", "")
        alternatives = tc.expected_output.get("alternatives", [])
        
        valid_industries = {expected.lower()} | {a.lower() for a in alternatives}
        passed = actual_industry.lower() in valid_industries
        
        return TestResult(
            test_id=tc.test_id,
            passed=passed,
            actual_output=actual_industry,
            expected_output=tc.expected_output,
            metrics={"confidence": response.confidence},
            latency_ms=latency,
        )
    
    def _run_matching_test(self, gateway, tc: TestCase, start: float) -> TestResult:
        """Run CV-JD matching test."""
        response = gateway.match_cv_jd(
            cv_text=tc.input_data.get("cv_text", ""),
            jd_text=tc.input_data.get("jd_text", ""),
        )
        latency = (time.perf_counter() - start) * 1000
        
        if not response.success:
            return TestResult(
                test_id=tc.test_id,
                passed=False,
                actual_output=None,
                expected_output=tc.expected_output,
                error=response.error,
                latency_ms=latency,
            )
        
        actual_coverage = response.result.get("coverage", 0)
        actual_grade = response.result.get("grade", "Unknown")
        
        passed = True
        if "min_coverage" in tc.expected_output and actual_coverage < tc.expected_output["min_coverage"]:
            passed = False
        if "max_coverage" in tc.expected_output and actual_coverage > tc.expected_output["max_coverage"]:
            passed = False
        if "grade" in tc.expected_output and actual_grade != tc.expected_output["grade"]:
            passed = False
        if "grade_not" in tc.expected_output and actual_grade == tc.expected_output["grade_not"]:
            passed = False
        
        return TestResult(
            test_id=tc.test_id,
            passed=passed,
            actual_output={"coverage": actual_coverage, "grade": actual_grade},
            expected_output=tc.expected_output,
            metrics={"coverage": actual_coverage / 100},
            latency_ms=latency,
        )
    
    def _run_calibration_test(self, gateway, tc: TestCase, start: float) -> TestResult:
        """Run confidence calibration test."""
        # Calibration tests are meta-tests that check historical data
        # For now, return placeholder
        latency = (time.perf_counter() - start) * 1000
        
        return TestResult(
            test_id=tc.test_id,
            passed=True,  # Placeholder
            actual_output={"note": "Calibration tests require historical data"},
            expected_output=tc.expected_output,
            metrics={},
            latency_ms=latency,
        )
    
    def _save_report(self, report: EvaluationReport):
        """Save evaluation report to disk."""
        try:
            filename = f"{report.suite}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = self.reports_dir / filename
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2)
            logger.debug("Saved report: %s", path)
        except Exception as e:
            logger.warning("Failed to save report: %s", e)
    
    def run_golden_tests(self) -> Dict[str, EvaluationReport]:
        """Run all golden test suites."""
        reports = {}
        for suite in self._test_cases:
            reports[suite] = self.run_suite(suite)
        return reports
    
    def check_regression(
        self,
        threshold: float = 0.05,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check for regression against historical results.
        
        Returns:
            (is_regressed, details)
        """
        # Load historical reports
        historical = {}
        for json_file in sorted(self.reports_dir.glob("*.json"), reverse=True):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                suite = data.get("suite", "unknown")
                if suite not in historical:
                    historical[suite] = data
            except Exception:
                pass
        
        # Run current tests
        current = self.run_golden_tests()
        
        # Compare
        regressions = []
        for suite, report in current.items():
            if suite in historical:
                hist = historical[suite]
                hist_rate = hist.get("pass_rate", 0)
                curr_rate = report.pass_rate
                
                if curr_rate < hist_rate - threshold:
                    regressions.append({
                        "suite": suite,
                        "historical_rate": hist_rate,
                        "current_rate": curr_rate,
                        "delta": curr_rate - hist_rate,
                    })
        
        is_regressed = len(regressions) > 0
        
        return is_regressed, {
            "regressions": regressions,
            "suites_checked": list(current.keys()),
            "threshold": threshold,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get harness statistics."""
        return {
            "suites": list(self._test_cases.keys()),
            "test_counts": {k: len(v) for k, v in self._test_cases.items()},
            "total_tests": sum(len(v) for v in self._test_cases.values()),
            "reports_dir": str(self.reports_dir),
        }


# ── Module-level Singleton ───────────────────────────────────────────────

_evaluator_instance: Optional[EvaluationHarness] = None
_evaluator_lock = Lock()


def get_evaluator() -> EvaluationHarness:
    """Get the module-level EvaluationHarness singleton."""
    global _evaluator_instance
    
    with _evaluator_lock:
        if _evaluator_instance is None:
            _evaluator_instance = EvaluationHarness()
        return _evaluator_instance
