#!/usr/bin/env python3
"""
CareerTrojan runtime wiring discovery
-------------------------------------

Purpose:
- Discover FastAPI routes
- Trace likely route -> service -> AI/module wiring
- Detect AI/orchestrator/model signals
- Generate markdown + JSON outputs for grounded architecture review

Usage:
    python tools/discover_runtime_wiring.py .
    python tools/discover_runtime_wiring.py /path/to/repo

Outputs:
    discovery_output/runtime_wiring_map.md
    discovery_output/routes.json
    discovery_output/service_calls.json
    discovery_output/ai_signals.json
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


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

ROUTE_DECORATORS = {"get", "post", "put", "patch", "delete", "options", "head"}

AI_KEYWORDS = {
    "ai",
    "model",
    "ml",
    "bayes",
    "bayesian",
    "regression",
    "classifier",
    "clustering",
    "similarity",
    "embedding",
    "vector",
    "inference",
    "orchestrator",
    "engine",
    "predict",
    "score",
    "ranking",
    "feature_registry",
    "context_assembler",
    "intelligence",
    "governance",
    "trained",
    "training",
    "unified_ai_engine",
}

SERVICE_HINTS = (
    "service",
    "services",
    "router",
    "engine",
    "client",
    "connector",
    "manager",
    "handler",
    "processor",
    "parser",
    "scorer",
)


@dataclass
class RouteRecord:
    file: str
    router_variable: str
    method: str
    path: str
    function_name: str
    prefix: str = ""
    tags: list[str] = field(default_factory=list)
    called_names: list[str] = field(default_factory=list)
    attribute_calls: list[str] = field(default_factory=list)
    ai_signals: list[str] = field(default_factory=list)
    likely_services: list[str] = field(default_factory=list)


@dataclass
class ServiceCallRecord:
    file: str
    function_name: str
    called_names: list[str]
    attribute_calls: list[str]
    ai_signals: list[str]


@dataclass
class AISignalRecord:
    file: str
    matched_terms: list[str]
    matched_lines: list[str]


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if not should_skip(path):
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def safe_parse(path: Path, text: str) -> ast.AST | None:
    try:
        return ast.parse(text, filename=str(path))
    except SyntaxError:
        return None


def get_constant_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    return None


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


class ModuleAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: Path, repo_root: Path):
        self.file_path = file_path
        self.repo_root = repo_root
        self.router_prefixes: dict[str, str] = {}
        self.router_tags: dict[str, list[str]] = {}
        self.routes: list[RouteRecord] = []
        self.service_calls: list[ServiceCallRecord] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        if isinstance(node.value, ast.Call):
            func_name = dotted_name(node.value.func)
            if func_name and func_name.endswith("APIRouter"):
                prefix = ""
                tags: list[str] = []
                for kw in node.value.keywords:
                    if kw.arg == "prefix":
                        prefix = get_constant_str(kw.value) or ""
                    elif kw.arg == "tags" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for elt in kw.value.elts:
                            value = get_constant_str(elt)
                            if value:
                                tags.append(value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.router_prefixes[target.id] = prefix
                        self.router_tags[target.id] = tags
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        called_names: list[str] = []
        attribute_calls: list[str] = []

        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                name = dotted_name(subnode.func)
                if name:
                    if "." in name:
                        attribute_calls.append(name)
                    else:
                        called_names.append(name)

        ai_signals = infer_ai_signals(called_names, attribute_calls)

        is_route_handler = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                router_obj = dotted_name(dec.func.value)
                method = dec.func.attr.lower()
                if router_obj and method in ROUTE_DECORATORS:
                    is_route_handler = True
                    path = ""
                    if dec.args:
                        path = get_constant_str(dec.args[0]) or ""
                    for kw in dec.keywords:
                        if kw.arg == "path":
                            path = get_constant_str(kw.value) or path
                    prefix = self.router_prefixes.get(router_obj, "")
                    tags = self.router_tags.get(router_obj, [])
                    likely_services = infer_likely_services(called_names, attribute_calls)
                    self.routes.append(
                        RouteRecord(
                            file=str(self.file_path.relative_to(self.repo_root)),
                            router_variable=router_obj,
                            method=method.upper(),
                            path=path,
                            function_name=node.name,
                            prefix=prefix,
                            tags=tags,
                            called_names=sorted(set(called_names)),
                            attribute_calls=sorted(set(attribute_calls)),
                            ai_signals=ai_signals,
                            likely_services=likely_services,
                        )
                    )
                    continue

        if is_route_handler:
            return

        if any(hint in node.name.lower() for hint in SERVICE_HINTS) or ai_signals:
            self.service_calls.append(
                ServiceCallRecord(
                    file=str(self.file_path.relative_to(self.repo_root)),
                    function_name=node.name,
                    called_names=sorted(set(called_names)),
                    attribute_calls=sorted(set(attribute_calls)),
                    ai_signals=ai_signals,
                )
            )


def infer_ai_signals(called_names: list[str], attribute_calls: list[str]) -> list[str]:
    haystack = " ".join(called_names + attribute_calls).lower()
    return sorted({kw for kw in AI_KEYWORDS if kw in haystack})


def infer_likely_services(called_names: list[str], attribute_calls: list[str]) -> list[str]:
    candidates = []
    for name in called_names + attribute_calls:
        lowered = name.lower()
        if any(h in lowered for h in SERVICE_HINTS):
            candidates.append(name)
    return sorted(set(candidates))


def scan_ai_signals(file_path: Path, repo_root: Path, text: str) -> AISignalRecord | None:
    matched_terms = sorted({kw for kw in AI_KEYWORDS if kw in text.lower()})
    if not matched_terms:
        return None

    lines = []
    raw_lines = text.splitlines()
    for i, line in enumerate(raw_lines, start=1):
        lowered = line.lower()
        if any(term in lowered for term in matched_terms):
            snippet = line.strip()
            if snippet:
                lines.append(f"L{i}: {snippet}")
        if len(lines) >= 10:
            break

    return AISignalRecord(
        file=str(file_path.relative_to(repo_root)),
        matched_terms=matched_terms,
        matched_lines=lines,
    )


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(
    repo_root: Path,
    routes: list[RouteRecord],
    service_calls: list[ServiceCallRecord],
    ai_records: list[AISignalRecord],
) -> str:
    route_count = len(routes)
    ai_route_count = sum(1 for r in routes if r.ai_signals)
    service_count = len(service_calls)
    ai_file_count = len(ai_records)

    lines: list[str] = []
    lines.append("# CareerTrojan Runtime Wiring Map")
    lines.append("")
    lines.append(f"Repository root: `{repo_root}`")
    lines.append("")
    lines.append("## Discovery summary")
    lines.append("")
    lines.append(f"- Route handlers discovered: **{route_count}**")
    lines.append(f"- Route handlers with AI-related call signals: **{ai_route_count}**")
    lines.append(f"- Service-like functions discovered: **{service_count}**")
    lines.append(f"- Python files with AI/model/orchestration keywords: **{ai_file_count}**")
    lines.append("")
    lines.append("## 1. Route to service discovery")
    lines.append("")
    lines.append("| Method | Full Path | Route Function | File | Likely Services / Calls | AI Signals |")
    lines.append("|---|---|---|---|---|---|")

    for route in sorted(routes, key=lambda r: (r.file, r.prefix + r.path, r.method)):
        full_path = f"{route.prefix}{route.path}"
        services = md_escape_cell(", ".join(route.likely_services[:6]) or "-")
        ai = md_escape_cell(", ".join(route.ai_signals) or "-")
        fn_name = md_escape_cell(route.function_name)
        file_name = md_escape_cell(route.file)
        path_cell = md_escape_cell(full_path)
        lines.append(
            f"| {route.method} | `{path_cell}` | `{fn_name}` | `{file_name}` | {services} | {ai} |"
        )

    lines.append("")
    lines.append("## 2. AI-bearing routes")
    lines.append("")
    if ai_route_count == 0:
        lines.append("No route handlers contained obvious AI call signals in this static pass.")
    else:
        for route in sorted([r for r in routes if r.ai_signals], key=lambda r: (r.file, r.function_name)):
            lines.append(f"### `{route.method} {route.prefix}{route.path}`")
            lines.append(f"- File: `{route.file}`")
            lines.append(f"- Function: `{route.function_name}`")
            lines.append(f"- AI signals: {', '.join(route.ai_signals)}")
            if route.likely_services:
                lines.append(f"- Likely services/calls: {', '.join(route.likely_services[:10])}")
            if route.attribute_calls:
                lines.append(f"- Attribute calls: {', '.join(route.attribute_calls[:12])}")
            lines.append("")

    lines.append("## 3. Service and orchestration signals")
    lines.append("")
    for record in sorted(service_calls, key=lambda r: (r.file, r.function_name))[:150]:
        lines.append(f"### `{record.function_name}` — `{record.file}`")
        lines.append(f"- AI signals: {', '.join(record.ai_signals) if record.ai_signals else '-'}")
        if record.attribute_calls:
            lines.append(f"- Attribute calls: {', '.join(record.attribute_calls[:15])}")
        if record.called_names:
            lines.append(f"- Direct calls: {', '.join(record.called_names[:15])}")
        lines.append("")

    lines.append("## 4. AI keyword bearing files")
    lines.append("")
    for record in sorted(ai_records, key=lambda r: (len(r.matched_terms), r.file), reverse=True)[:200]:
        lines.append(f"### `{record.file}`")
        lines.append(f"- Matched terms: {', '.join(record.matched_terms)}")
        for line in record.matched_lines[:8]:
            lines.append(f"  - {line}")
        lines.append("")

    lines.append("## 5. What to inspect manually next")
    lines.append("")
    lines.append("Focus first on these categories:")
    lines.append("")
    lines.append("1. Route handlers whose call chains include `service`, `router`, `engine`, `predict`, `score`, `inference`, or `orchestrator`")
    lines.append("2. Files with names such as `unified_ai_engine.py`, `orchestrator.py`, `router.py`, `feature_registry.py`, `context_assembler.py`")
    lines.append("3. Frontend pages that call analysis, scoring, insight, structural, radar, or chart endpoints")
    lines.append("4. Any places where runtime routes bypass the advanced engine and fall back to simple heuristics")
    lines.append("")
    lines.append("## 6. Limits of this static pass")
    lines.append("")
    lines.append("- This script is static analysis, not runtime tracing")
    lines.append("- Dynamic imports, dependency injection, and factory-created services may not be fully resolved")
    lines.append("- It identifies likely wiring and hotspots, then shortens the manual review path")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo path does not exist: {repo_root}")
        return 1

    out_dir = repo_root / "discovery_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    routes: list[RouteRecord] = []
    service_calls: list[ServiceCallRecord] = []
    ai_records: list[AISignalRecord] = []

    for py_file in iter_py_files(repo_root):
        text = read_text(py_file)
        tree = safe_parse(py_file, text)

        ai_record = scan_ai_signals(py_file, repo_root, text)
        if ai_record:
            ai_records.append(ai_record)

        if tree is None:
            continue

        analyzer = ModuleAnalyzer(py_file, repo_root)
        analyzer.visit(tree)
        routes.extend(analyzer.routes)
        service_calls.extend(analyzer.service_calls)

    write_json(out_dir / "routes.json", [asdict(r) for r in routes])
    write_json(out_dir / "service_calls.json", [asdict(s) for s in service_calls])
    write_json(out_dir / "ai_signals.json", [asdict(a) for a in ai_records])

    md = render_markdown(repo_root, routes, service_calls, ai_records)
    (out_dir / "runtime_wiring_map.md").write_text(md, encoding="utf-8")

    print("Discovery complete.")
    print(f"Repo: {repo_root}")
    print(f"Routes found: {len(routes)}")
    print(f"Service-like functions found: {len(service_calls)}")
    print(f"AI-bearing files found: {len(ai_records)}")
    print(f"Output folder: {out_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
