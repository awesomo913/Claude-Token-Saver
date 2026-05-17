# From: claude_backend/http_server.py:50
# Where Token Saver writes per-project memory files.

def _claude_projects_dir() -> Path:
    """Where Token Saver writes per-project memory files."""
    return Path.home() / ".claude" / "projects"
