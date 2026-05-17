# From: claude_backend/http_server.py:118
# Write origin.txt for an existing slug that lacked one — so the

def _cache_origin_txt(slug_dir: Path, real_path: str) -> None:
    """Write origin.txt for an existing slug that lacked one — so the
    next /projects call hits step 1 and avoids the filesystem walk.

    Refuses to write if `slug_dir` isn't directly under the Claude
    projects dir — defensive guard against a path-traversal slug name
    redirecting the write outside the expected tree.
    """
    if slug_dir.parent != _claude_projects_dir():
        logger.debug(
            "origin.txt cache skipped: %s is outside %s",
            slug_dir, _claude_projects_dir(),
        )
        return
    try:
        (slug_dir / "origin.txt").write_text(real_path, encoding="utf-8")
    except OSError as e:
        logger.debug("origin.txt cache write failed for %s: %s", slug_dir.name, e)
