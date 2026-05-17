"""Extract and organize reusable code snippets into a library."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..types import CodeBlock, ProjectAnalysis

logger = logging.getLogger(__name__)

# "# From: <relative/path.py>:<lineno>"
_HEADER_RE = re.compile(r"^#\s*From:\s*(.+?):(\d+)\s*$")

_KIND_BY_DIR = {
    "utilities": "function",
    "classes": "class",
    "patterns": "function",
}


def generate_snippet_library(
    analysis: ProjectAnalysis,
    max_lines: int = 100,
) -> dict[str, str]:
    """Generate snippet files organized by category.

    Returns dict of relative_path -> content for all snippets + INDEX.md.
    """
    snippets: dict[str, str] = {}
    utilities: list[CodeBlock] = []
    classes: list[CodeBlock] = []
    patterns: list[CodeBlock] = []

    # "method" was excluded prior to 2026-05 — class-heavy projects
    # (e.g. claude_backend itself) had ZERO indexed coverage. Grader
    # bottomed out at 30% hit rate on this project as a result.
    # Include methods alongside free functions so retrieval sees them.
    _CALLABLE_KINDS = ("function", "async_function", "method")
    # Private underscore-prefix filter dropped, since codebases like
    # this one use _handle_pending / _show_picker / _copy_context as
    # the main internal API — exactly what users ask about.
    for block in analysis.blocks:
        lines = block.end_line - block.start_line + 1
        # Skip very small blocks (one-liners aren't useful snippets).
        if lines < 3:
            continue

        # Two separate size budgets: classes get 150 (full small classes
        # stay readable), callables get max_lines (default 50). The
        # previous code applied max_lines as a single gate up top, which
        # silently dropped every 50<lines<=150 class — including
        # TokenTracker, OverlayButton, SearchIndex.
        if block.kind == "class" and lines <= 150:
            classes.append(block)
        elif block.kind in _CALLABLE_KINDS and lines <= max_lines and block.docstring:
            utilities.append(block)
        elif block.kind in _CALLABLE_KINDS and lines <= max_lines and _is_pattern(block):
            patterns.append(block)

    # Write utility snippets. Caps were 30/20/15 — too small for
    # multi-package projects (everything past the first ~80 utilities
    # dropped silently). Grader hit 30% recall on claude_backend until
    # the cap was raised; now 250/100/100, which still keeps the
    # inverted index well under smart_search's cache thresholds.
    for i, block in enumerate(utilities[:250]):
        path = f"utilities/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        if block.docstring:
            header += f"# {block.docstring.split(chr(10))[0].strip()}\n"
        snippets[path] = header + "\n" + block.source

    # Write class snippets.
    for i, block in enumerate(classes[:100]):
        path = f"classes/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        snippets[path] = header + "\n" + block.source

    # Write pattern snippets.
    for i, block in enumerate(patterns[:100]):
        path = f"patterns/{_safe_name(block.name)}.py"
        header = f"# From: {block.file_path}:{block.start_line}\n"
        snippets[path] = header + "\n" + block.source

    # Generate INDEX.md
    if snippets:
        snippets["INDEX.md"] = _build_index(utilities, classes, patterns)

    return snippets


def write_snippet_library(
    analysis: ProjectAnalysis,
    max_lines: int = 100,
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


def load_snippet_library(base: Path) -> list[CodeBlock]:
    """Read .claude/snippets/*/*.py back into CodeBlocks for search.

    Inverse of write_snippet_library. Each file has a "# From: path:line"
    header (optionally followed by "# <docstring>") and then source.
    Returns [] if base missing or no parseable files. Never raises.
    """
    if not base.is_dir():
        return []

    blocks: list[CodeBlock] = []
    for sub in ("utilities", "classes", "patterns"):
        kind = _KIND_BY_DIR[sub]
        sub_dir = base / sub
        if not sub_dir.is_dir():
            continue
        for file in sorted(sub_dir.glob("*.py")):
            try:
                text = file.read_text(encoding="utf-8")
            except OSError as e:
                logger.warning("Cannot read snippet %s: %s", file, e)
                continue

            lines = text.splitlines()
            if not lines:
                continue

            header_match = _HEADER_RE.match(lines[0])
            if not header_match:
                logger.warning("Snippet %s missing '# From: ...' header, skipping", file)
                continue
            file_path = header_match.group(1).strip()
            try:
                start_line = int(header_match.group(2))
            except ValueError:
                logger.warning("Snippet %s has non-integer line in header, skipping", file)
                continue

            cursor = 1
            docstring: str | None = None
            if cursor < len(lines) and lines[cursor].startswith("#"):
                docstring = lines[cursor].lstrip("# ").strip() or None
                cursor += 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1

            source = "\n".join(lines[cursor:]).rstrip()
            if not source:
                continue

            blocks.append(CodeBlock(
                name=file.stem,
                kind=kind,
                source=source,
                start_line=start_line,
                end_line=start_line + source.count("\n"),
                docstring=docstring,
                file_path=file_path,
            ))

    return blocks


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
        for block in utilities[:250]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](utilities/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if classes:
        lines.append("## Classes\n")
        for block in classes[:100]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](classes/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    if patterns:
        lines.append("## Patterns\n")
        for block in patterns[:100]:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(f"- [`{block.name}`](patterns/{_safe_name(block.name)}.py)"
                        f" (from `{block.file_path}:{block.start_line}`){doc}")
        lines.append("")

    return "\n".join(lines)
