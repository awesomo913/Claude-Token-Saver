# From: claude_backend/generators/snippet_library.py:102
# Write snippet library to project's .claude/snippets/ directory.

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
