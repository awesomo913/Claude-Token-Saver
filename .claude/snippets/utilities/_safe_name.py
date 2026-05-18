# From: claude_backend/generators/snippet_library.py:201
# Sanitize a name for use as a filename.

def _safe_name(name: str) -> str:
    """Sanitize a name for use as a filename."""
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return safe[:60] or "unnamed"
