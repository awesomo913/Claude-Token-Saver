# From: claude_backend/scanners/project.py:200
# Count files by extension.

def get_language_stats(entries: list[FileEntry]) -> dict[str, int]:
    """Count files by extension."""
    stats: dict[str, int] = {}
    for e in entries:
        stats[e.ext] = stats.get(e.ext, 0) + 1
    return dict(sorted(stats.items(), key=lambda x: -x[1]))
