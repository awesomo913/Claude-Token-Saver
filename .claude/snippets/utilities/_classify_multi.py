# From: claude_backend/analyzers/pattern_detector.py:143
# Pick the dominant style from multiple options.

def _classify_multi(*pairs: tuple[str, int]) -> str:
    """Pick the dominant style from multiple options."""
    total = sum(c for _, c in pairs)
    if total == 0:
        return "none"
    top_label, top_count = max(pairs, key=lambda x: x[1])
    if top_count / total > 0.6:
        return top_label
    return "mixed"
