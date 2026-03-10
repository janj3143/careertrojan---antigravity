#!/usr/bin/env python3
"""
CareerTrojan full wiring discovery
----------------------------------

Purpose:
- Discover frontend API calls
- Discover backend FastAPI routes
- Match frontend calls to backend routes
- Detect likely service / AI hotspots
- Generate readable markdown and JSON outputs

Usage:
    python tools/discover_full_wiring.py .
    python tools/discover_full_wiring.py /path/to/repo

Outputs:
    discovery_output/full_wiring_map.md
    discovery_output/frontend_api_calls.json
    discovery_output/backend_routes.json
    discovery_output/frontend_to_backend_matches.json
    discovery_output/service_ai_hotspots.json
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

FRONTEND_EXTS = {".ts", ".tsx", ".js", ".jsx"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


@dataclass
class BackendRoute:
    file: str
    router_variable: str
    method: str
    path: str
    prefix: str = ""
    function_name: str = ""
    tags: list[str] = field(default_factory=list)
    called_names: list[str] = field(default_factory=list)
    attribute_calls: list[str] = field(default_factory=list)
    ai_signals: list[str] = field(default_factory=list)
    likely_services: list[str] = field(default_factory=list)

    @property
    def full_path(self) -> str:
        return normalize_path(f"{self.prefix}{self.path}")


@dataclass
class FrontendCall:
    file: str
    line_no: int
    method: str
    path: str
    source: str
    inferred_component: str = ""
    portal: str = ""
    matched_backend_routes: list[str] = field(default_factory=list)


@dataclass
class MatchRecord:
    frontend_file: str
    line_no: int
    portal: str
    method: str
    frontend_path: str
    backend_matches: list[str]
    backend_files: list[str]
    backend_functions: list[str]
    backend_ai_signals: list[str]
    likely_services: list[str]


@dataclass
class ServiceHotspot:
    file: str
    function_name: str
    called_names: list[str]
    attribute_calls: list[str]
    ai_signals: list[str]


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_files(root: Path, suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune excluded and symlinked directories early to keep traversal stable.
        pruned = []
        for d in dirnames:
            if d in EXCLUDED_DIRS:
                continue
            full = Path(dirpath) / d
            try:
                if full.is_symlink():
                    continue
            except OSError:
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for name in filenames:
            full = Path(dirpath) / name
            try:
                if full.suffix.lower() in suffixes and not should_skip(full):
                    files.append(full)
            except OSError:
                continue
    return files


def iter_py_files(root: Path) -> list[Path]:
    return iter_files(root, {".py"})


def iter_frontend_files(root: Path) -> list[Path]:
    return iter_files(root, FRONTEND_EXTS)


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


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    path = re.sub(r"/+", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def path_to_regex(path: str) -> re.Pattern[str]:
    normalized = normalize_path(path)
    pattern = re.sub(r"\{[^/]+\}", r"[^/]+", normalized)
    pattern = "^" + pattern + "$"
    return re.compile(pattern)


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


def detect_portal(path: Path) -> str:
    s = str(path).lower()
    if "admin-portal" in s or "apps/admin" in s.replace("\\", "/"):
        return "admin"
    if "mentor-portal" in s or "apps/mentor" in s.replace("\\", "/"):
        return "mentor"
    if "user-portal" in s or "apps/user" in s.replace("\\", "/"):
        return "user"
    return "unknown"


class BackendAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: Path, repo_root: Path):
        self.file_path = file_path
        self.repo_root = repo_root
        self.router_prefixes: dict[str, str] = {}
        self.router_tags: dict[str, list[str]] = {}
        self.routes: list[BackendRoute] = []
        self.hotspots: list[ServiceHotspot] = []

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

        is_route = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                router_obj = dotted_name(dec.func.value)
                method = dec.func.attr.lower()
                if router_obj and method in ROUTE_DECORATORS:
                    is_route = True
                    path = ""
                    if dec.args:
                        path = get_constant_str(dec.args[0]) or ""
                    for kw in dec.keywords:
                        if kw.arg == "path":
                            path = get_constant_str(kw.value) or path

                    self.routes.append(
                        BackendRoute(
                            file=str(self.file_path.relative_to(self.repo_root)),
                            router_variable=router_obj,
                            method=method.upper(),
                            path=path,
                            prefix=self.router_prefixes.get(router_obj, ""),
                            function_name=node.name,
                            tags=self.router_tags.get(router_obj, []),
                            called_names=sorted(set(called_names)),
                            attribute_calls=sorted(set(attribute_calls)),
                            ai_signals=ai_signals,
                            likely_services=infer_likely_services(called_names, attribute_calls),
                        )
                    )
        if is_route:
            return

        if any(hint in node.name.lower() for hint in SERVICE_HINTS) or ai_signals:
            self.hotspots.append(
                ServiceHotspot(
                    file=str(self.file_path.relative_to(self.repo_root)),
                    function_name=node.name,
                    called_names=sorted(set(called_names)),
                    attribute_calls=sorted(set(attribute_calls)),
                    ai_signals=ai_signals,
                )
            )


def discover_backend(repo_root: Path) -> tuple[list[BackendRoute], list[ServiceHotspot]]:
    routes: list[BackendRoute] = []
    hotspots: list[ServiceHotspot] = []

    for py_file in iter_py_files(repo_root):
        text = read_text(py_file)
        tree = safe_parse(py_file, text)
        if tree is None:
            continue
        analyzer = BackendAnalyzer(py_file, repo_root)
        analyzer.visit(tree)
        routes.extend(analyzer.routes)
        hotspots.extend(analyzer.hotspots)

    return routes, hotspots


def detect_component_name(text: str, line_index: int) -> str:
    lines = text.splitlines()
    start = max(0, line_index - 40)
    for i in range(line_index, start, -1):
        line = lines[i]
        m1 = re.search(r"\bfunction\s+([A-Z][A-Za-z0-9_]*)\b", line)
        if m1:
            return m1.group(1)
        m2 = re.search(r"\bconst\s+([A-Z][A-Za-z0-9_]*)\s*[:=].*=>", line)
        if m2:
            return m2.group(1)
        m3 = re.search(r"\bexport\s+default\s+function\s+([A-Z][A-Za-z0-9_]*)\b", line)
        if m3:
            return m3.group(1)
    return ""


def extract_frontend_calls(file_path: Path, repo_root: Path) -> list[FrontendCall]:
    text = read_text(file_path)
    calls: list[FrontendCall] = []
    portal = detect_portal(file_path)

    patterns = [
        re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']\s*(?:,\s*\{[^}]*method\s*:\s*[\"']([A-Za-z]+)[\"'])?", re.I | re.S),
        re.compile(r"\baxios\.(get|post|put|patch|delete|options|head)\(\s*[\"']([^\"']+)[\"']", re.I),
        re.compile(r"\b([A-Za-z0-9_$.]+)\.(get|post|put|patch|delete|options|head)\(\s*[\"']([^\"']+)[\"']", re.I),
        re.compile(r"method\s*:\s*[\"']([A-Za-z]+)[\"']\s*,\s*url\s*:\s*[\"']([^\"']+)[\"']", re.I | re.S),
        re.compile(r"url\s*:\s*[\"']([^\"']+)[\"']\s*,\s*method\s*:\s*[\"']([A-Za-z]+)[\"']", re.I | re.S),
    ]

    lines = text.splitlines()

    for idx, line in enumerate(lines):
        for pattern in patterns:
            for match in pattern.finditer(line):
                if pattern.pattern.startswith("fetch"):
                    path = match.group(1)
                    method = (match.group(2) or "GET").upper()
                    source = "fetch"
                elif "axios" in pattern.pattern and pattern.pattern.startswith(r"\baxios"):
                    method = match.group(1).upper()
                    path = match.group(2)
                    source = "axios"
                elif "url" in pattern.pattern and pattern.pattern.startswith("method"):
                    method = match.group(1).upper()
                    path = match.group(2)
                    source = "config"
                elif "url" in pattern.pattern and pattern.pattern.startswith("url"):
                    path = match.group(1)
                    method = match.group(2).upper()
                    source = "config"
                else:
                    source_obj = match.group(1)
                    method = match.group(2).upper()
                    path = match.group(3)
                    source = source_obj

                if not path.startswith("/"):
                    continue

                calls.append(
                    FrontendCall(
                        file=str(file_path.relative_to(repo_root)),
                        line_no=idx + 1,
                        method=method if method in HTTP_METHODS else "GET",
                        path=normalize_path(path),
                        source=source,
                        inferred_component=detect_component_name(text, idx),
                        portal=portal,
                    )
                )

    joined = "\n".join(lines)
    multiline_patterns = [
        re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']\s*,\s*\{(.*?)\}\s*\)", re.I | re.S),
        re.compile(r"\baxios\.(get|post|put|patch|delete|options|head)\(\s*[\"']([^\"']+)[\"']", re.I | re.S),
    ]

    seen = {(c.file, c.line_no, c.method, c.path, c.source) for c in calls}

    for pattern in multiline_patterns:
        for match in pattern.finditer(joined):
            start_pos = match.start()
            line_no = joined.count("\n", 0, start_pos) + 1

            if pattern.pattern.startswith("fetch"):
                path = normalize_path(match.group(1))
                config_blob = match.group(2)
                m = re.search(r"method\s*:\s*[\"']([A-Za-z]+)[\"']", config_blob, re.I)
                method = (m.group(1).upper() if m else "GET")
                source = "fetch"
            else:
                method = match.group(1).upper()
                path = normalize_path(match.group(2))
                source = "axios"

            key = (str(file_path.relative_to(repo_root)), line_no, method, path, source)
            if key in seen:
                continue

            calls.append(
                FrontendCall(
                    file=str(file_path.relative_to(repo_root)),
                    line_no=line_no,
                    method=method if method in HTTP_METHODS else "GET",
                    path=path,
                    source=source,
                    inferred_component=detect_component_name(text, max(0, line_no - 1)),
                    portal=portal,
                )
            )
            seen.add(key)

    dedup: dict[tuple[str, int, str, str, str], FrontendCall] = {}
    for c in calls:
        dedup[(c.file, c.line_no, c.method, c.path, c.source)] = c

    # If a fetch callsite/path has both inferred GET and explicit non-GET methods,
    # keep only explicit methods to avoid method-inference false positives.
    grouped_methods: dict[tuple[str, int, str, str], set[str]] = {}
    for c in dedup.values():
        key = (c.file, c.line_no, c.path, c.source)
        grouped_methods.setdefault(key, set()).add(c.method)

    filtered: list[FrontendCall] = []
    for c in dedup.values():
        key = (c.file, c.line_no, c.path, c.source)
        methods = grouped_methods.get(key, set())
        if c.method == "GET" and any(m != "GET" for m in methods):
            continue
        filtered.append(c)

    return sorted(filtered, key=lambda x: (x.file, x.line_no, x.path, x.method))


def discover_frontend(repo_root: Path) -> list[FrontendCall]:
    calls: list[FrontendCall] = []
    for file_path in iter_frontend_files(repo_root):
        calls.extend(extract_frontend_calls(file_path, repo_root))
    return calls


def match_frontend_to_backend(
    frontend_calls: list[FrontendCall],
    backend_routes: list[BackendRoute],
) -> list[MatchRecord]:
    matches: list[MatchRecord] = []

    indexed_routes: list[tuple[BackendRoute, re.Pattern[str]]] = [
        (route, path_to_regex(route.full_path)) for route in backend_routes
    ]

    for call in frontend_calls:
        call_path = normalize_path(call.path)
        matched: list[BackendRoute] = []

        for route, route_regex in indexed_routes:
            if route.method != call.method:
                continue
            if route_regex.match(call_path):
                matched.append(route)
                continue

            if route.full_path.endswith(call_path) or call_path.endswith(route.full_path):
                matched.append(route)

        if matched:
            call.matched_backend_routes = [r.full_path for r in matched]

            ai_signals = sorted({sig for r in matched for sig in r.ai_signals})
            services = sorted({svc for r in matched for svc in r.likely_services})
            matches.append(
                MatchRecord(
                    frontend_file=call.file,
                    line_no=call.line_no,
                    portal=call.portal,
                    method=call.method,
                    frontend_path=call.path,
                    backend_matches=[r.full_path for r in matched],
                    backend_files=sorted({r.file for r in matched}),
                    backend_functions=sorted({r.function_name for r in matched}),
                    backend_ai_signals=ai_signals,
                    likely_services=services,
                )
            )

    return matches


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(
    repo_root: Path,
    frontend_calls: list[FrontendCall],
    backend_routes: list[BackendRoute],
    matches: list[MatchRecord],
    hotspots: list[ServiceHotspot],
) -> str:
    matched_count = len(matches)
    frontend_count = len(frontend_calls)
    backend_count = len(backend_routes)
    ai_match_count = sum(1 for m in matches if m.backend_ai_signals)

    lines: list[str] = []
    lines.append("# CareerTrojan Full Wiring Map")
    lines.append("")
    lines.append(f"Repository root: `{repo_root}`")
    lines.append("")
    lines.append("## Discovery summary")
    lines.append("")
    lines.append(f"- Frontend API calls discovered: **{frontend_count}**")
    lines.append(f"- Backend FastAPI routes discovered: **{backend_count}**")
    lines.append(f"- Frontend calls matched to backend routes: **{matched_count}**")
    lines.append(f"- Matched flows with backend AI signals: **{ai_match_count}**")
    lines.append("")
    lines.append("## 1. Frontend -> backend matched flows")
    lines.append("")
    lines.append("| Portal | Frontend File | Line | Method | Frontend Path | Backend Match | AI Signals | Likely Services |")
    lines.append("|---|---|---:|---|---|---|---|---|")

    for m in sorted(matches, key=lambda x: (x.portal, x.frontend_file, x.line_no, x.frontend_path)):
        backend_match = "<br>".join(f"`{md_escape_cell(p)}`" for p in m.backend_matches[:4]) or "-"
        ai = md_escape_cell(", ".join(m.backend_ai_signals[:8]) or "-")
        svcs = md_escape_cell(", ".join(m.likely_services[:8]) or "-")
        lines.append(
            f"| {md_escape_cell(m.portal)} | `{md_escape_cell(m.frontend_file)}` | {m.line_no} | {m.method} | `{md_escape_cell(m.frontend_path)}` | {backend_match} | {ai} | {svcs} |"
        )

    lines.append("")
    lines.append("## 2. Unmatched frontend API calls")
    lines.append("")

    matched_keys = {(m.frontend_file, m.line_no, m.method, m.frontend_path) for m in matches}
    unmatched = [
        c for c in frontend_calls
        if (c.file, c.line_no, c.method, c.path) not in matched_keys
    ]

    if not unmatched:
        lines.append("All discovered frontend calls matched at least one backend route in this pass.")
    else:
        lines.append("| Portal | File | Line | Method | Path | Source | Component |")
        lines.append("|---|---|---:|---|---|---|---|")
        for c in sorted(unmatched, key=lambda x: (x.portal, x.file, x.line_no)):
            lines.append(
                f"| {md_escape_cell(c.portal)} | `{md_escape_cell(c.file)}` | {c.line_no} | {c.method} | `{md_escape_cell(c.path)}` | {md_escape_cell(c.source)} | {md_escape_cell(c.inferred_component or '-')} |"
            )

    lines.append("")
    lines.append("## 3. Backend routes with AI signals")
    lines.append("")
    ai_routes = [r for r in backend_routes if r.ai_signals]
    if not ai_routes:
        lines.append("No backend routes with obvious AI call signals were found in this static pass.")
    else:
        for r in sorted(ai_routes, key=lambda x: (x.file, x.full_path, x.function_name)):
            lines.append(f"### `{r.method} {r.full_path}`")
            lines.append(f"- File: `{r.file}`")
            lines.append(f"- Function: `{r.function_name}`")
            lines.append(f"- AI signals: {', '.join(r.ai_signals)}")
            if r.likely_services:
                lines.append(f"- Likely services: {', '.join(r.likely_services[:12])}")
            if r.attribute_calls:
                lines.append(f"- Attribute calls: {', '.join(r.attribute_calls[:14])}")
            lines.append("")

    lines.append("## 4. Service / orchestration hotspots")
    lines.append("")
    for h in sorted(hotspots, key=lambda x: (x.file, x.function_name))[:200]:
        if not h.ai_signals and not any("service" in n.lower() or "engine" in n.lower() for n in h.attribute_calls):
            continue
        lines.append(f"### `{h.function_name}` - `{h.file}`")
        lines.append(f"- AI signals: {', '.join(h.ai_signals) if h.ai_signals else '-'}")
        if h.attribute_calls:
            lines.append(f"- Attribute calls: {', '.join(h.attribute_calls[:15])}")
        if h.called_names:
            lines.append(f"- Direct calls: {', '.join(h.called_names[:15])}")
        lines.append("")

    lines.append("## 5. Priority manual review targets")
    lines.append("")
    lines.append("Review these first:")
    lines.append("")
    lines.append("1. Matched frontend flows where backend AI signals appear")
    lines.append("2. Unmatched frontend calls, because they often reveal stale endpoints, proxy-only paths, or incomplete migrations")
    lines.append("3. Backend routes that call `service`, `router`, `engine`, `predict`, `score`, or `orchestrator`")
    lines.append("4. Files named like `unified_ai_engine.py`, `orchestrator.py`, `router.py`, `feature_registry.py`, `context_assembler.py`")
    lines.append("")
    lines.append("## 6. Limits of this pass")
    lines.append("")
    lines.append("- Static analysis only; it does not execute the runtime")
    lines.append("- Client wrappers and environment-based base URLs may hide some matches")
    lines.append("- Dynamic route generation and dependency injection may require manual confirmation")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo path does not exist: {repo_root}")
        return 1

    out_dir = repo_root / "discovery_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    backend_routes, hotspots = discover_backend(repo_root)
    frontend_calls = discover_frontend(repo_root)
    matches = match_frontend_to_backend(frontend_calls, backend_routes)

    write_json(out_dir / "frontend_api_calls.json", [asdict(c) for c in frontend_calls])
    write_json(out_dir / "backend_routes.json", [asdict(r) for r in backend_routes])
    write_json(out_dir / "frontend_to_backend_matches.json", [asdict(m) for m in matches])
    write_json(out_dir / "service_ai_hotspots.json", [asdict(h) for h in hotspots])

    md = render_markdown(repo_root, frontend_calls, backend_routes, matches, hotspots)
    (out_dir / "full_wiring_map.md").write_text(md, encoding="utf-8")

    print("Full wiring discovery complete.")
    print(f"Repo: {repo_root}")
    print(f"Frontend API calls: {len(frontend_calls)}")
    print(f"Backend routes: {len(backend_routes)}")
    print(f"Matches: {len(matches)}")
    print(f"Output folder: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
