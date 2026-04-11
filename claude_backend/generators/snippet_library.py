"""Extract and organize reusable code snippets into a library."""

from __future__ import annotations

import logging
from pathlib import Path

from ..types import CodeBlock, ProjectAnalysis

logger = logging.getLogger(__name__)


def generate_snippet_library(
    analysis: ProjectAnalysis,
    max_lines: int = 50,
) -> dict[str, str]:
    """Generate snippet files organized by category.

    Returns dict of relative_path -> content for all snippets + INDEX.md.
    """
    snippets: dict[str, str] = {}
    utilities: list[CodeBlock] = []
    classes: list[CodeBlock] = []
    patterns: list[CodeBlock] = []

    for block in analysis.blocks:
        lines = block.end_line - block.start_line + 1
        if lines > max_lines:
            continue
        # Skip private code — not reusable
        if block.name.startswith("_"):
            continue
        # Skip very small blocks (one-liners aren't useful snippets)
        if lines < 3:
            continue

        if block.kind == "class" and lines <= 150:
            classes.append(block)
        elif block.kind in ("function", "async_function") and block.docstring:
            utilities.append(block)
        elif block.kind in ("function", "async_function") and _is_pattern(block):
            patterns.append(block)

    # Write utility snippets
    for i, block in enumerate(utilities[:30]):
        path = f"utilities/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        if block.docstring:
            header += f"# {block.docstring.split(chr(10))[0].strip()}\n"
        snippets[path] = header + "\n" + block.source

    # Write class snippets
    for i, block in enumerate(classes[:20]):
        path = f"classes/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        snippets[path] = header + "\n" + block.source

    # Write pattern snippets
    for i, block in enumerate(patterns[:15]):
        path = f"patterns/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        snippets[path] = header + "\n" + block.source

    # Generate INDEX.md
    if snippets:
        snippets["INDEX.md"] = _build_index(utilities, classes, patterns)

    return snippets


def write_snippet_library(
    analysis: ProjectAnalysis,
    max_lines: int = 50,
) -> list[str]:
    """Write snippet library to project's .claude/snippets/ directory.

    Returns list of written file paths.
    """
    snippets = generate_snippet_library(analysis, max_lines)
    if not snippets:
        return []

    base = analysis.root / ".claude" / "snippets"
    written: list[str] = []

    for rel_path, content in snippets.items():
        full = base / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        written.append(str(full))

    logger.info("Wrote %d snippets to %s", len(snippets), base)
    return written


def _is_pattern(block: CodeBlock) -> bool:
    """Check if a function looks like a reusable pattern."""
    pattern_indicators = [
        "setup", "configure", "init", "create", "build",
        "parse", "load", "save", "validate", "format",
        "connect", "retry", "wrap", "decorate", "register",
    ]
    name_lower = block.name.lower()
    return any(ind in name_lower for ind in pattern_indicators)


def _safe_name(name: str) -> str:
    """Sanitize a name for use as a filename."""
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return safe[:60] or "unnamed"


def _build_index(
    utilities: list[CodeBlock],
    classes: list[CodeBlock],
    patterns: list[CodeBlock],
) -> str:
    lines = ["# Snippet Library\n"]

    if utilities:
        lines.append("## Utilities\n")
        for block in utilities[:30]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](utilities/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if classes:
        lines.append("## Classes\n")
        for block in classes[:20]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](classes/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if patterns:
        lines.append("## Patterns\n")
        for block in patterns[:15]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](patterns/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    return "\n".join(lines)
