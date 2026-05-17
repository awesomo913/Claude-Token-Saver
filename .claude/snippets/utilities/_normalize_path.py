# From: claude_backend/storage.py:85
# Normalize a relative or absolute path into clean segments.

def _normalize_path(rel_path: str) -> list[str]:
    """Normalize a relative or absolute path into clean segments.

    Handles Windows drive letters, mixed separators, and path traversal.
    """
    p = rel_path.replace("\\", "/")

    # Strip Windows drive letter (e.g., "C:/Users/..." -> "Users/...")
    if len(p) >= 2 and p[1] == ":":
        p = p[2:]

    # Split and filter dangerous/empty segments
    parts = [
        seg for seg in PurePosixPath(p).parts
        if seg not in (".", "..", "/", "") and seg != "/"
    ]
    return parts
