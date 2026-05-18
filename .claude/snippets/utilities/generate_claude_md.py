# From: claude_backend/generators/claude_md.py:16
# Generate CLAUDE.md content from a ProjectAnalysis.

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
