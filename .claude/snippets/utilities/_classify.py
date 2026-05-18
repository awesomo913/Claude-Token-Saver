# From: claude_backend/analyzers/pattern_detector.py:118
# Classify between two options based on counts.

def _classify(a_count: int, b_count: int, a_label: str, b_label: str) -> str:
    """Classify between two options based on counts."""
    total = a_count + b_count
    if total == 0:
        return "none"
    ratio = a_count / total
    if ratio > 0.7:
        return a_label
    if ratio < 0.3:
        return b_label
    return "mixed"
