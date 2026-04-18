"""Generate Claude Code memory files for persistent cross-session context."""

from __future__ import annotations

import logging
from pathlib import Path

from ..types import ConventionReport, ModuleInfo, ProjectAnalysis

logger = logging.getLogger(__name__)


def compute_project_slug(project_path: Path) -> str:
    """Compute the Claude Code project slug from an absolute path.

    Claude Code converts: separators -> dashes, colons -> dashes, spaces -> dashes.
    C:\\Users\\foo bar -> C--Users-foo-bar
    """
    resolved = str(project_path.resolve())
    slug = resolved.replace("\\", "-").replace("/", "-").replace(":", "-").replace(" ", "-")
    return slug


def get_memory_dirs(project_path: Path) -> tuple[Path, Path]:
    """Return (claude_code_memory_dir, project_memory_dir)."""
    slug = compute_project_slug(project_path)
    claude_code_dir = Path.home() / ".claude" / "projects" / slug / "memory"
    project_dir = project_path / ".claude" / "memory"
    return claude_code_dir, project_dir


def generate_memory_files(analysis: ProjectAnalysis) -> dict[str, str]:
    """Generate all memory file contents as a dict of filename -> content."""
    files: dict[str, str] = {}

    files["reference_architecture.md"] = _gen_architecture(analysis)
    files["reference_patterns.md"] = _gen_patterns(analysis)
    files["reference_utilities.md"] = _gen_utilities(analysis)
    files["project_conventions.md"] = _gen_conventions(analysis)
    hot = _gen_hot_functions(analysis)
    if hot:
        files["hot_functions.md"] = hot
    files["MEMORY.md"] = _gen_index(files)

    return files


def _gen_hot_functions(analysis: ProjectAnalysis) -> str:
    """Generate a 'hot functions' memory file from session_context.json.

    Lists the functions the user has most recently and most frequently
    added to their context. Claude auto-loads this, so their most-used
    code is already in context without manual intervention.
    """
    import json
    from collections import Counter

    session_path = analysis.root / ".claude" / "session_context.json"
    if not session_path.is_file():
        return ""

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    history = data.get("context_history", [])
    if not history:
        return ""

    # Count usage per function name
    usage = Counter()
    sources = {}
    for entry in history:
        name = entry.get("name", "")
        src = entry.get("source", "") or entry.get("file_path", "")
        if name:
            usage[name] += 1
            if name not in sources:
                sources[name] = src

    if not usage:
        return ""

    # Top 15 most-used functions
    top = usage.most_common(15)

    lines = [
        "---",
        f"name: {analysis.name} Hot Functions",
        f"description: Most-referenced code in recent sessions",
        "type: reference",
        "---",
        "",
        f"# Frequently Referenced Code ({analysis.name})",
        "",
        "These are the functions/classes you reference most often when working",
        "on this project. Keep them in mind for upcoming work.",
        "",
        "| Function/Class | Source File | Times Used |",
        "|---|---|---|",
    ]
    for name, count in top:
        src = sources.get(name, "?")
        lines.append(f"| `{name}` | `{src}` | {count} |")

    lines.append("")
    return "\n".join(lines)


def write_memory_files(analysis: ProjectAnalysis) -> list[str]:
    """Write memory files to both Claude Code dir and project dir.

    Returns list of written file paths.
    """
    files = generate_memory_files(analysis)
    claude_dir, project_dir = get_memory_dirs(analysis.root)

    written: list[str] = []
    for target_dir in [claude_dir, project_dir]:
        target_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            path = target_dir / filename
            path.write_text(content, encoding="utf-8")
            written.append(str(path))

    logger.info("Wrote %d memory files to 2 locations", len(files))
    return written


# ---------------------------------------------------------------------------
# Individual generators
# ---------------------------------------------------------------------------

def _gen_architecture(analysis: ProjectAnalysis) -> str:
    lines = [
        "---",
        f"name: {analysis.name} Architecture",
        f"description: Module map and dependency graph for {analysis.name}",
        "type: reference",
        "---",
        "",
        f"# {analysis.name} Architecture",
        "",
    ]

    # Group modules by top-level directory
    packages: dict[str, list[ModuleInfo]] = {}
    for mod in analysis.modules:
        parts = mod.path.split("/")
        pkg = parts[0] if len(parts) > 1 else "(root)"
        packages.setdefault(pkg, []).append(mod)

    for pkg_name in sorted(packages.keys()):
        mods = packages[pkg_name]
        lines.append(f"## {pkg_name}/")
        lines.append("")

        for mod in sorted(mods, key=lambda m: m.path):
            purpose = ""
            if mod.docstring:
                first = mod.docstring.split("\n")[0].strip()
                if first:
                    purpose = f": {first}"
            names = ", ".join(mod.public_names[:8]) if mod.public_names else ""
            names_str = f" | exports: {names}" if names else ""
            lines.append(f"- `{mod.path}`{purpose}{names_str}")

            if mod.imports:
                imp_str = ", ".join(mod.imports[:5])
                lines.append(f"  - imports: {imp_str}")

        lines.append("")

    return "\n".join(lines)


def _gen_patterns(analysis: ProjectAnalysis) -> str:
    conv = analysis.conventions
    lines = [
        "---",
        f"name: {analysis.name} Patterns",
        f"description: Common code patterns and error handling in {analysis.name}",
        "type: reference",
        "---",
        "",
        f"# Code Patterns in {analysis.name}",
        "",
    ]

    if conv.error_handling != "none":
        lines.append("## Error Handling")
        lines.append(f"- Primary style: {conv.error_handling}")
        if conv.error_handling == "specific":
            lines.append("- Uses specific exception types (OSError, ValueError, etc.)")
        elif conv.error_handling == "bare":
            lines.append("- WARNING: bare `except:` used -- consider narrowing")
        elif conv.error_handling == "broad":
            lines.append("- Uses `except Exception` -- may hide bugs")
        lines.append("")

    if conv.logging_style != "none":
        lines.append("## Logging")
        lines.append(f"- Primary style: {conv.logging_style}")
        if conv.logging_style == "logging":
            lines.append("- Pattern: `logger = logging.getLogger(__name__)`")
        lines.append("")

    if conv.path_style != "none":
        lines.append("## Path Handling")
        lines.append(f"- Primary style: {conv.path_style}")
        lines.append("")

    if conv.import_style != "unknown":
        lines.append("## Import Style")
        lines.append(f"- Primary style: {conv.import_style}")
        lines.append("")

    return "\n".join(lines)


def _gen_utilities(analysis: ProjectAnalysis) -> str:
    lines = [
        "---",
        f"name: {analysis.name} Utilities",
        f"description: Reusable functions and their locations in {analysis.name}",
        "type: reference",
        "---",
        "",
        f"# Reusable Functions in {analysis.name}",
        "",
        "| Function | Module | Purpose |",
        "|----------|--------|---------|",
    ]

    for mod in analysis.modules:
        if not mod.public_names:
            continue
        for name in mod.public_names[:10]:
            # Find the matching block for docstring
            doc = ""
            for block in analysis.blocks:
                if block.file_path == mod.path and block.name == name:
                    if block.docstring:
                        doc = block.docstring.split("\n")[0].strip()
                    break
            if not doc:
                doc = "--"
            lines.append(f"| `{name}` | `{mod.path}` | {doc} |")

    lines.append("")
    return "\n".join(lines)


def _gen_conventions(analysis: ProjectAnalysis) -> str:
    conv = analysis.conventions
    lines = [
        "---",
        f"name: {analysis.name} Conventions",
        f"description: Detected coding standards for {analysis.name}",
        "type: project",
        "---",
        "",
        f"# Coding Conventions ({analysis.name})",
        "",
        f"Analyzed {conv.samples_analyzed} Python files.",
        "",
        f"- **Path handling**: {conv.path_style}",
        f"- **Type hints**: {conv.type_hints}",
        f"- **String formatting**: {conv.string_format}",
        f"- **Error handling**: {conv.error_handling}",
        f"- **Logging**: {conv.logging_style}",
        f"- **Imports**: {conv.import_style}",
        "",
    ]

    # Actionable rules
    lines.append("## Rules to follow")
    lines.append("")
    if conv.path_style == "pathlib":
        lines.append("- Use `pathlib.Path` for all new path operations")
    if conv.type_hints in ("heavy", "light"):
        lines.append("- Add type hints to new functions")
    if conv.string_format == "f-string":
        lines.append("- Use f-strings for string formatting")
    if conv.error_handling == "specific":
        lines.append("- Catch specific exceptions, not bare `except`")
    if conv.logging_style == "logging":
        lines.append("- Use `logger = logging.getLogger(__name__)`, not print()")

    lines.append("")
    return "\n".join(lines)


def _gen_index(files: dict[str, str]) -> str:
    """Generate MEMORY.md index."""
    lines = []
    file_descs = {
        "reference_architecture.md": "Module map and dependency graph",
        "reference_patterns.md": "Common code patterns and error handling",
        "reference_utilities.md": "Reusable functions with locations",
        "project_conventions.md": "Detected coding standards and rules",
    }
    for filename, desc in file_descs.items():
        if filename in files:
            lines.append(f"- [{filename.replace('.md', '').replace('_', ' ').title()}]({filename}) -- {desc}")

    return "\n".join(lines) + "\n"
