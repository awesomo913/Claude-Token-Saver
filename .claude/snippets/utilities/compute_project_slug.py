# From: claude_backend/generators/memory_files.py:23
# Compute the Claude Code project slug from an absolute path.

def compute_project_slug(project_path: Path) -> str:
    """Compute the Claude Code project slug from an absolute path.

    Claude Code converts: separators -> dashes, colons -> dashes, spaces -> dashes.
    C:\\Users\\foo bar -> C--Users-foo-bar
    """
    resolved = str(project_path.resolve())
    slug = resolved.replace("\\", "-").replace("/", "-").replace(":", "-").replace(" ", "-")
    return slug
