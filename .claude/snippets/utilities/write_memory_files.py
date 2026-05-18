# From: claude_backend/generators/memory_files.py:121
# Write memory files to both Claude Code dir and project dir.

def write_memory_files(analysis: ProjectAnalysis) -> list[str]:
    """Write memory files to both Claude Code dir and project dir.

    Also writes an origin.txt next to the Claude Code memory dir
    recording the original absolute project path. The slug-based
    directory name is lossy (path separators, colons, and spaces all
    collapse to dashes), so origin.txt is the authoritative reverse-
    lookup used by http_server's /projects endpoint.

    Returns list of written file paths.
    """
    files = generate_memory_files(analysis)
    claude_dir, project_dir = get_memory_dirs(analysis.root)

    written: list[str] = []
    for target_dir in [claude_dir, project_dir]:
        target_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            path = target_dir / filename
            # v0.7.0 — never overwrite preserved files. Bootstrap
            # regeneration must not clobber hand-maintained context
            # like session_notes.md.
            if filename in _PRESERVED_FILES and path.is_file():
                logger.debug("preserved file kept: %s", path)
                continue
            path.write_text(content, encoding="utf-8")
            written.append(str(path))

    # Write origin.txt at the slug dir's parent (sibling of memory/) so
    # /projects can recover the real path without slug-reverse-mangling.
    try:
        origin = claude_dir.parent / "origin.txt"
        origin.write_text(str(analysis.root.resolve()), encoding="utf-8")
    except OSError as e:
        logger.debug("Failed to write origin.txt: %s", e)

    logger.info("Wrote %d memory files to 2 locations", len(files))
    return written
