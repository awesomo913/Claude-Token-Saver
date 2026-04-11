"""Detect coding conventions and patterns by sampling Python files."""

from __future__ import annotations

import ast
import logging

from ..types import ConventionReport, FileEntry

logger = logging.getLogger(__name__)

MAX_SAMPLES = 20


def detect_conventions(entries: list[FileEntry]) -> ConventionReport:
    """Analyze Python files to detect coding conventions."""
    py_files = [e for e in entries if e.ext == ".py"]
    samples = py_files[:MAX_SAMPLES]

    if not samples:
        return ConventionReport(samples_analyzed=0)

    counts = {
        "pathlib": 0, "os_path": 0,
        "type_hints": 0, "no_type_hints": 0,
        "f_string": 0, "format_method": 0, "percent_format": 0,
        "specific_except": 0, "bare_except": 0, "broad_except": 0,
        "logging_module": 0, "print_calls": 0,
        "absolute_import": 0, "relative_import": 0,
    }

    for entry in samples:
        try:
            tree = ast.parse(entry.content)
        except SyntaxError:
            continue
        _analyze_tree(tree, entry.content, counts)

    report = ConventionReport(samples_analyzed=len(samples))
    report.path_style = _classify(counts["pathlib"], counts["os_path"], "pathlib", "os.path")
    report.type_hints = _classify_presence(counts["type_hints"], counts["no_type_hints"], "heavy", "light", "none")
    report.string_format = _classify_multi(
        ("f-string", counts["f_string"]),
        ("format", counts["format_method"]),
        ("percent", counts["percent_format"]),
    )
    report.error_handling = _classify_multi(
        ("specific", counts["specific_except"]),
        ("bare", counts["bare_except"]),
        ("broad", counts["broad_except"]),
    )
    report.logging_style = _classify(counts["logging_module"], counts["print_calls"], "logging", "print")
    report.import_style = _classify(counts["absolute_import"], counts["relative_import"], "absolute", "relative")
    report.details = counts

    return report


def _analyze_tree(tree: ast.AST, source: str, counts: dict) -> None:
    """Walk an AST and tally convention indicators."""
    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pathlib" or alias.name.startswith("pathlib."):
                    counts["pathlib"] += 1
                if alias.name == "os.path" or alias.name == "os":
                    counts["os_path"] += 1
                if alias.name == "logging":
                    counts["logging_module"] += 1

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "pathlib" or module.startswith("pathlib."):
                counts["pathlib"] += 1
            if module in ("os", "os.path"):
                counts["os_path"] += 1
            if module == "logging":
                counts["logging_module"] += 1
            if node.level and node.level > 0:
                counts["relative_import"] += 1
            else:
                counts["absolute_import"] += 1

        # Type hints on functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_hints = node.returns is not None or any(
                a.annotation is not None for a in node.args.args
            )
            if has_hints:
                counts["type_hints"] += 1
            else:
                counts["no_type_hints"] += 1

        # Exception handling
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                counts["bare_except"] += 1
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                counts["broad_except"] += 1
            else:
                counts["specific_except"] += 1

        # Print calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                counts["print_calls"] += 1

    # F-strings (check source text since AST doesn't distinguish)
    if "f'" in source or 'f"' in source:
        counts["f_string"] += 1
    if ".format(" in source:
        counts["format_method"] += 1
    if "% " in source or "%s" in source or "%d" in source:
        counts["percent_format"] += 1


def _classify(a_count: int, b_count: int, a_label: str, b_label: str) -> str:
    """Classify between two options based on counts."""
    total = a_count + b_count
    if total == 0:
        return "none"
    ratio = a_count / total
    if ratio > 0.7:
        return a_label
    if ratio < 0.3:
        return b_label
    return "mixed"


def _classify_presence(pos: int, neg: int, heavy: str, light: str, none: str) -> str:
    total = pos + neg
    if total == 0:
        return none
    ratio = pos / total
    if ratio > 0.6:
        return heavy
    if ratio > 0.2:
        return light
    return none


def _classify_multi(*pairs: tuple[str, int]) -> str:
    """Pick the dominant style from multiple options."""
    total = sum(c for _, c in pairs)
    if total == 0:
        return "none"
    top_label, top_count = max(pairs, key=lambda x: x[1])
    if top_count / total > 0.6:
        return top_label
    return "mixed"
