"""Extract and organize reusable code snippets into a library."""

from __future__ import annotations

import logging
import re
from pathlib import Path, PurePosixPath

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

    # Dedupe + assign collision-safe filenames BEFORE applying the cap.
    # Without this, ~half the utilities pool is gemini_coder_web/* copies
    # of root-level files (browser_actions.py, broadcast.py etc.) that
    # crowd out unique symbols like build_menu and generate_memory_files.
    # Filename collisions also silently overwrote distinct callables
    # sharing a short name (`main`, `load`, `save`).
    # Cap utilities at 350 (was 250). After dedup recovered ~100 slots,
    # there's still a 435-callable pool and useful symbols like
    # build_menu (pos 305) + generate_memory_files (pos 328) sat past
    # the old cap. 350 covers them with headroom; smart_search inverted
    # index still O(candidates), well under perf thresholds.
    utility_writes = _dedupe_and_assign_paths(utilities, "utilities")[:350]
    class_writes = _dedupe_and_assign_paths(classes, "classes")[:100]
    pattern_writes = _dedupe_and_assign_paths(patterns, "patterns")[:100]

    # Docstring header MUST be written for every kind. load_snippet_library
    # reads the second `# ...` line as block.docstring; without it, classes
    # and patterns round-trip as docstring=None, losing the ranker's
    # ×1.3 doc-length bonus and the doc-word match contributions.
    def _make(block: CodeBlock) -> str:
        header = f"# From: {block.file_path}:{block.start_line}\n"
        if block.docstring:
            header += f"# {block.docstring.split(chr(10))[0].strip()}\n"
        return header + "\n" + block.source

    for block, path in utility_writes:
        snippets[path] = _make(block)
    for block, path in class_writes:
        snippets[path] = _make(block)
    for block, path in pattern_writes:
        snippets[path] = _make(block)

    if snippets:
        snippets["INDEX.md"] = _build_index(
            utility_writes, class_writes, pattern_writes,
        )

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


def _dedupe_and_assign_paths(
    blocks: list[CodeBlock], subdir: str,
) -> list[tuple[CodeBlock, str]]:
    """Collapse content-duplicates and assign collision-safe filenames.

    Two stages:
      1. Dedupe by (name, source-stripped). Prefer the block whose
         file_path is shorter (less nested = more canonical).
      2. Assign `<subdir>/<safe_name>.py` to each kept block. On
         collision, prefix with parent dir (`<subdir>/<parent>__<name>.py`)
         and fall back to a numeric suffix for any residual clash.

    Preserves the original ordering of kept blocks so the cap-slice
    applied by the caller still sees blocks in traversal order.
    """
    # Pass 1: dedupe — last writer wins for same shape, but we re-check
    # which file_path is shorter, so canonical location is kept.
    canonical: dict[tuple[str, str], CodeBlock] = {}
    for b in blocks:
        key = (b.name, b.source.strip())
        existing = canonical.get(key)
        if existing is None or len(b.file_path) < len(existing.file_path):
            canonical[key] = b
    kept_ids = {id(b) for b in canonical.values()}
    deduped = [b for b in blocks if id(b) in kept_ids]

    # Pass 2: assign safe paths with collision disambiguation.
    out: list[tuple[CodeBlock, str]] = []
    used: set[str] = set()
    for b in deduped:
        base = _safe_name(b.name)
        path = f"{subdir}/{base}.py"
        if path in used:
            parent = PurePosixPath(b.file_path.replace("\\", "/")).parent.name or "_root"
            parent_safe = _safe_name(parent)
            path = f"{subdir}/{parent_safe}__{base}.py"
            n = 2
            while path in used:
                path = f"{subdir}/{parent_safe}__{base}_{n}.py"
                n += 1
        used.add(path)
        out.append((b, path))
    return out


def _build_index(
    utility_writes: list[tuple[CodeBlock, str]],
    class_writes: list[tuple[CodeBlock, str]],
    pattern_writes: list[tuple[CodeBlock, str]],
) -> str:
    lines = ["# Snippet Library\n"]

    def _section(title: str, writes: list[tuple[CodeBlock, str]]) -> None:
        if not writes:
            return
        lines.append(f"## {title}\n")
        for block, path in writes:
            doc = ""
            if block.docstring:
                doc = f" -- {block.docstring.split(chr(10))[0].strip()}"
            lines.append(
                f"- [`{block.name}`]({path})"
                f" (from `{block.file_path}:{block.start_line}`){doc}"
            )
        lines.append("")

    _section("Utilities", utility_writes)
    _section("Classes", class_writes)
    _section("Patterns", pattern_writes)

    return "\n".join(lines)
