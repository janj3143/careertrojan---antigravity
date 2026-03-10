#!/usr/bin/env python3
"""
CareerTrojan signal lifecycle discovery (v3)

Purpose:
- Inventory extracted signals/features
- Find likely model/rule consumers of those signals
- Find likely execution consequences (returned payloads / outputs)
- Generate lifecycle report artifacts

Outputs:
  discovery_output/signal_inventory.json
  discovery_output/signal_consumers.json
  discovery_output/signal_execution_map.json
  discovery_output/signal_lifecycle_report.md
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
    "coverage",
    "htmlcov",
    "site-packages",
}

EXCLUDED_PATH_PREFIXES = (
    "tools/",
    "tests/",
    "scripts/",
    "docs/",
    "discovery_output/",
)

SIGNAL_NAME_HINTS = (
    "signal",
    "feature",
    "features",
    "feature_bundle",
    "indicator",
    "indicators",
    "traits",
    "score_inputs",
    "parsed_resume",
    "match_features",
    "confidence_features",
    "overlap",
    "density",
    "fit_score",
    "confidence",
    "progression",
    "impact",
)

EXTRACTION_FN_HINTS = (
    "extract_",
    "build_features",
    "assemble_context",
    "compute_signals",
    "derive_features",
    "parse_",
    "normalize_",
)

RESPONSE_FN_HINTS = (
    "predict",
    "classify",
    "rank",
    "adjust_weight",
    "apply_rules",
    "infer",
    "evaluate",
    "score",
)

EXECUTION_TARGET_HINTS = (
    "return",
    "response",
    "payload",
    "chart",
    "visual",
    "recommend",
    "summary",
    "alert",
    "notify",
    "workflow",
    "state",
    "store",
    "save",
)


@dataclass
class SignalRecord:
    signal: str
    extracted_in_file: str
    extracted_in_function: str
    extraction_type: str
    line_hint: int | None = None


@dataclass
class SignalConsumer:
    signal: str
    consumed_in_file: str
    consumed_in_function: str
    consumer_type: str
    evidence: str


@dataclass
class SignalExecution:
    signal: str
    execution_in_file: str
    execution_in_function: str
    affects: list[str] = field(default_factory=list)
    visible_in: list[str] = field(default_factory=list)


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def is_noise_file(path: Path, repo_root: Path) -> bool:
    rel = str(path.relative_to(repo_root)).replace("\\", "/").lower()
    if any(rel.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return True
    return rel.endswith("_test.py") or "/test_" in rel


def iter_source_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            p = Path(dirpath) / f
            if should_skip(p):
                continue
            if is_noise_file(p, root):
                continue
            if p.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                out.append(p)
    return out


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def looks_like_signal_name(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in SIGNAL_NAME_HINTS)


def fn_type(name: str) -> str:
    n = name.lower()
    if any(h in n for h in EXTRACTION_FN_HINTS):
        return "extraction"
    if any(h in n for h in RESPONSE_FN_HINTS):
        return "response"
    return "generic"


def extract_py_signals(path: Path, repo_root: Path) -> tuple[list[SignalRecord], dict[str, list[tuple[str, str, str]]], dict[str, list[tuple[str, str, str]]]]:
    text = read_text(path)
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return [], {}, {}

    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    records: list[SignalRecord] = []
    consumers: dict[str, list[tuple[str, str, str]]] = {}
    executions: dict[str, list[tuple[str, str, str]]] = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fname = node.name
            ftype = fn_type(fname)

            created_signals: set[str] = set()

            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name) and looks_like_signal_name(t.id):
                            created_signals.add(t.id)
                            records.append(
                                SignalRecord(
                                    signal=t.id,
                                    extracted_in_file=rel,
                                    extracted_in_function=fname,
                                    extraction_type=ftype,
                                    line_hint=getattr(sub, "lineno", None),
                                )
                            )

                if isinstance(sub, ast.Call):
                    call_name = ""
                    if isinstance(sub.func, ast.Name):
                        call_name = sub.func.id
                    elif isinstance(sub.func, ast.Attribute):
                        call_name = sub.func.attr

                    c_lower = call_name.lower()
                    if any(h in c_lower for h in RESPONSE_FN_HINTS):
                        for arg in sub.args:
                            if isinstance(arg, ast.Name) and looks_like_signal_name(arg.id):
                                consumers.setdefault(arg.id, []).append((rel, fname, call_name))

                if isinstance(sub, ast.Subscript):
                    if isinstance(sub.value, ast.Name) and looks_like_signal_name(sub.value.id):
                        consumers.setdefault(sub.value.id, []).append((rel, fname, "subscript_use"))

                if isinstance(sub, ast.Return):
                    ret_txt = ast.unparse(sub.value) if hasattr(ast, "unparse") and sub.value is not None else ""
                    low = ret_txt.lower()
                    if any(h in low for h in EXECUTION_TARGET_HINTS):
                        for sig in created_signals:
                            executions.setdefault(sig, []).append((rel, fname, "return_payload"))

            # Generic usage fallback for created signals in response-like functions.
            if ftype == "response":
                node_src = ast.get_source_segment(text, node) or ""
                node_low = node_src.lower()
                for sig in created_signals:
                    if sig.lower() in node_low:
                        consumers.setdefault(sig, []).append((rel, fname, "response_fn_context"))

    return records, consumers, executions


def extract_frontend_visibility(path: Path, repo_root: Path, known_signals: set[str]) -> dict[str, list[tuple[str, str, str]]]:
    text = read_text(path)
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    vis: dict[str, list[tuple[str, str, str]]] = {}

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if not any(h in low for h in ("chart", "visual", "spider", "covey", "recommend", "summary")):
            continue
        for sig in known_signals:
            if sig.lower() in low:
                vis.setdefault(sig, []).append((rel, f"line_{i}", "ui_visibility"))

    # fallback broad reference
    file_low = text.lower()
    if any(k in file_low for k in ("spider", "covey", "chart", "visual")):
        for sig in known_signals:
            if sig.lower() in file_low:
                vis.setdefault(sig, []).append((rel, "file_scope", "ui_visibility"))

    return vis


def dedupe_triples(items: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    seen = set()
    out = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo path does not exist: {repo_root}")
        return 1

    out_dir = repo_root / "discovery_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = iter_source_files(repo_root)
    py_files = [p for p in files if p.suffix.lower() == ".py"]
    fe_files = [p for p in files if p.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"}]

    signal_records: list[SignalRecord] = []
    consumer_map: dict[str, list[tuple[str, str, str]]] = {}
    execution_map: dict[str, list[tuple[str, str, str]]] = {}

    for p in py_files:
        recs, consumers, executions = extract_py_signals(p, repo_root)
        signal_records.extend(recs)
        for k, v in consumers.items():
            consumer_map.setdefault(k, []).extend(v)
        for k, v in executions.items():
            execution_map.setdefault(k, []).extend(v)

    signals = sorted({r.signal for r in signal_records})

    # Frontend visibility pass
    for p in fe_files:
        vis = extract_frontend_visibility(p, repo_root, set(signals))
        for sig, refs in vis.items():
            execution_map.setdefault(sig, []).extend(refs)

    # Dedupe maps
    for k in list(consumer_map):
        consumer_map[k] = dedupe_triples(consumer_map[k])
    for k in list(execution_map):
        execution_map[k] = dedupe_triples(execution_map[k])

    signal_inventory = [asdict(r) for r in signal_records]

    signal_consumers = []
    for sig, refs in sorted(consumer_map.items()):
        for file_, fn, ev in refs:
            signal_consumers.append(
                asdict(
                    SignalConsumer(
                        signal=sig,
                        consumed_in_file=file_,
                        consumed_in_function=fn,
                        consumer_type="model_or_rule_candidate",
                        evidence=ev,
                    )
                )
            )

    signal_execution = []
    for sig, refs in sorted(execution_map.items()):
        grouped_by_file: dict[tuple[str, str], list[str]] = {}
        for file_, fn, ev in refs:
            grouped_by_file.setdefault((file_, fn), []).append(ev)
        for (file_, fn), evs in grouped_by_file.items():
            signal_execution.append(
                asdict(
                    SignalExecution(
                        signal=sig,
                        execution_in_file=file_,
                        execution_in_function=fn,
                        affects=sorted(set(evs)),
                        visible_in=["api_payload_or_ui"],
                    )
                )
            )

    (out_dir / "signal_inventory.json").write_text(json.dumps(signal_inventory, indent=2), encoding="utf-8")
    (out_dir / "signal_consumers.json").write_text(json.dumps(signal_consumers, indent=2), encoding="utf-8")
    (out_dir / "signal_execution_map.json").write_text(json.dumps(signal_execution, indent=2), encoding="utf-8")

    # Report
    extracted_signals = len(signals)
    consumed_signals = len({r["signal"] for r in signal_consumers})
    executed_signals = len({r["signal"] for r in signal_execution})

    top_extracted = sorted(signals)[:60]

    lines: list[str] = []
    lines.append("# Signal Lifecycle Report")
    lines.append("")
    lines.append(f"Repository root: {repo_root}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Signals extracted: {extracted_signals}")
    lines.append(f"- Signals with consumer evidence: {consumed_signals}")
    lines.append(f"- Signals with execution/visibility evidence: {executed_signals}")
    lines.append("")
    lines.append("## Lifecycle Audit")
    lines.append("")
    lines.append("1. Signal extraction: variable and feature-like assignments discovered in Python functions")
    lines.append("2. Signal response: signal usage in predict/classify/rank/infer/evaluate/score contexts")
    lines.append("3. Signal execution: signal references in return payloads and frontend visual/output files")
    lines.append("4. Noise filtering: excludes tools/tests/scripts/docs/discovery outputs from analysis")
    lines.append("")
    lines.append("## Sample Signals")
    lines.append("")
    for sig in top_extracted:
        c = len(consumer_map.get(sig, []))
        e = len(execution_map.get(sig, []))
        lines.append(f"- {sig}: consumers={c}, executions={e}")

    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- discovery_output/signal_inventory.json")
    lines.append("- discovery_output/signal_consumers.json")
    lines.append("- discovery_output/signal_execution_map.json")
    lines.append("- discovery_output/signal_lifecycle_report.md")

    (out_dir / "signal_lifecycle_report.md").write_text("\n".join(lines), encoding="utf-8")

    print("Signal lifecycle discovery complete.")
    print(f"Repo: {repo_root}")
    print(f"Signals extracted: {extracted_signals}")
    print(f"Signals consumed: {consumed_signals}")
    print(f"Signals executed: {executed_signals}")
    print(f"Output folder: {out_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
