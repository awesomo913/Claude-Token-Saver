# From: claude_backend/overlay.py:66
# Score how likely proj matches the window the user was working in.

def _score_project(proj: dict, window_title: str) -> int:
    """Score how likely proj matches the window the user was working in."""
    if not window_title:
        return 0
    import re
    title_lower = window_title.lower()
    name = (proj.get("name") or proj.get("slug") or "").lower()
    path = (proj.get("path") or "").lower()

    score = 0
    if name and name in title_lower:
        score += 60
    # Last two path segments (most specific part of the path)
    path_parts = [p for p in re.split(r"[/\\]", path) if len(p) > 2]
    for part in path_parts[-2:]:
        if part in title_lower:
            score += 30
    # Token overlap between project name and title words
    title_tokens = set(re.split(r"[\s\-–|·/\\_.]+", title_lower)) - {"", "the", "a"}
    name_tokens = set(re.split(r"[\s\-_]+", name)) - {""}
    score += len(title_tokens & name_tokens) * 10
    return score
