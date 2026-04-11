"""Generate a CLAUDE.md file from project analysis."""

from __future__ import annotations

import logging
from pathlib import Path

from ..types import ConventionReport, ModuleInfo, ProjectAnalysis

logger = logging.getLogger(__name__)

MARKER_START = "<!-- claude-backend:generated:start -->"
MARKER_END = "<!-- claude-backend:generated:end -->"


def generate_claude_md(analysis: ProjectAnalysis, max_lines: int = 200) -> str:
    """Generate CLAUDE.md content from a ProjectAnalysis."""
    sections: list[str] = []

    # Header
    sections.append(f"# {analysis.name}\n")

    # Overview
    sections.append(_overview_section(analysis))

    # Directory structure
    sections.append(_structure_section(analysis))

    # Conventions
    if analysis.conventions.samples_analyzed > 0:
        sections.append(_conventions_section(analysis.conventions))

    # Module reference
    if analysis.modules:
        sections.append(_module_section(analysis.modules))

    # Snippet reference
    snippets_index = analysis.root / ".claude" / "snippets" / "INDEX.md"
    if snippets_index.is_file():
        sections.append("## Snippets\n\nSee `.claude/snippets/INDEX.md` for reusable code blocks.\n")

    content = "\n".join(sections)

    # Trim to max lines
    lines = content.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"\n<!-- Truncated to {max_lines} lines -->")
        content = "\n".join(lines)

    return content


def write_claude_md(analysis: ProjectAnalysis, max_lines: int = 200) -> bool:
    """Write or update CLAUDE.md at the project root.

    Preserves user-written content outside the generated markers.
    Returns True if file was written/updated.
    """
    generated = generate_claude_md(analysis, max_lines)
    wrapped = f"{MARKER_START}\n{generated}\n{MARKER_END}"

    target = analysis.root / "CLAUDE.md"

    if target.is_file():
        existing = target.read_text(encoding="utf-8", errors="replace")

        # Check for existing markers
        start_idx = existing.find(MARKER_START)
        end_idx = existing.find(MARKER_END)

        if start_idx != -1 and end_idx != -1:
            # Replace between markers
            end_idx += len(MARKER_END)
            new_content = existing[:start_idx] + wrapped + existing[end_idx:]
        else:
            # Append generated block
            new_content = existing.rstrip() + "\n\n" + wrapped + "\n"

        if new_content == existing:
            return False
        target.write_text(new_content, encoding="utf-8")
    else:
        target.write_text(wrapped + "\n", encoding="utf-8")

    logger.info("Wrote CLAUDE.md at %s", target)
    return True


def _overview_section(analysis: ProjectAnalysis) -> str:
    lines = ["## Overview\n"]

    # Languages
    if analysis.language_stats:
        top_langs = list(analysis.language_stats.items())[:5]
        lang_str = ", ".join(f"{ext} ({count})" for ext, count in top_langs)
        lines.append(f"- **Files**: {sum(analysis.language_stats.values())} ({lang_str})")

    # Entry points
    if analysis.entry_points:
        eps = ", ".join(f"`{e}`" for e in analysis.entry_points[:5])
        lines.append(f"- **Entry points**: {eps}")

    # Dependencies
    if analysis.dependencies:
        deps = ", ".join(analysis.dependencies[:10])
        lines.append(f"- **Dependencies**: {deps}")

    # Key files
    if analysis.key_files:
        keys = ", ".join(f"`{k}`" for k in analysis.key_files)
        lines.append(f"- **Key files**: {keys}")

    lines.append("")
    return "\n".join(lines)


def _structure_section(analysis: ProjectAnalysis) -> str:
    """Generate a 2-level directory tree."""
    lines = ["## Structure\n", "```"]

    # Build tree from file paths
    dirs: dict[str, dict[str, int]] = {}
    for f in analysis.files:
        parts = f.path.split("/")
        if len(parts) >= 2:
            top = parts[0]
            if top not in dirs:
                dirs[top] = {}
            if len(parts) >= 3:
                sub = parts[1]
                dirs[top][sub] = dirs[top].get(sub, 0) + 1
            else:
                dirs[top]["(files)"] = dirs[top].get("(files)", 0) + 1
        else:
            dirs.setdefault("(root)", {})
            dirs["(root)"]["(files)"] = dirs["(root)"].get("(files)", 0) + 1

    for top_dir in sorted(dirs.keys()):
        if top_dir == "(root)":
            continue
        sub_count = sum(dirs[top_dir].values())
        lines.append(f"{top_dir}/  ({sub_count} files)")
        subs = dirs[top_dir]
        for sub_name in sorted(subs.keys())[:8]:
            if sub_name == "(files)":
                continue
            lines.append(f"  {sub_name}/  ({subs[sub_name]} files)")

    lines.extend(["```", ""])
    return "\n".join(lines)


def _conventions_section(conv: ConventionReport) -> str:
    lines = ["## Conventions\n"]

    rules = []
    if conv.path_style == "pathlib":
        rules.append("Use `pathlib.Path` for all path operations")
    elif conv.path_style == "os.path":
        rules.append("Use `os.path` for path operations (legacy style)")

    if conv.type_hints == "heavy":
        rules.append("Type hints are used extensively -- maintain them")
    elif conv.type_hints == "light":
        rules.append("Type hints are used on some functions")

    if conv.string_format == "f-string":
        rules.append("Prefer f-strings for string formatting")

    if conv.error_handling == "specific":
        rules.append("Use specific exception types in except clauses")

    if conv.logging_style == "logging":
        rules.append("Use `logging.getLogger(__name__)` for all logging")
    elif conv.logging_style == "print":
        rules.append("Uses print() for output (consider migrating to logging)")

    if conv.import_style == "relative":
        rules.append("Relative imports used for intra-package references")
    elif conv.import_style == "absolute":
        rules.append("Absolute imports preferred")

    for rule in rules:
        lines.append(f"- {rule}")

    lines.append("")
    return "\n".join(lines)


def _module_section(modules: list[ModuleInfo]) -> str:
    lines = ["## Modules\n"]

    # Skip __init__.py and sort by path
    significant = [
        m for m in modules
        if not m.path.endswith("__init__.py") and not m.path.endswith("__main__.py")
    ]
    significant.sort(key=lambda m: m.path)

    for mod in significant[:40]:  # Cap at 40 modules
        purpose = ""
        if mod.docstring:
            # First sentence of docstring
            first_line = mod.docstring.split("\n")[0].strip().rstrip(".")
            if first_line:
                purpose = f" -- {first_line}"

        entry_marker = " [entry]" if mod.entry_point else ""
        lines.append(f"- `{mod.path}`{purpose}{entry_marker}")

    lines.append("")
    return "\n".join(lines)
