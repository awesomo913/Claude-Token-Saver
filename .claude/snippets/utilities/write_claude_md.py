# From: claude_backend/generators/claude_md.py:54
# Write or update CLAUDE.md at the project root.

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
