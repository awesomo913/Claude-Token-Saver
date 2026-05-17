# From: claude_backend/search.py:300
# Score 0.0-1.0 for how well query matches target.

def _fuzzy_match(query_word: str, target_word: str) -> float:
    """Score 0.0-1.0 for how well query matches target.

    Handles typos via SequenceMatcher.
    """
    if query_word == target_word:
        return 1.0
    if query_word in target_word or target_word in query_word:
        return 0.85
    # Stem match
    if _stem(query_word) == _stem(target_word):
        return 0.8
    # Fuzzy (typo tolerance) — generous threshold for sloppy typing
    ratio = SequenceMatcher(None, query_word, target_word).ratio()
    if ratio > 0.55:
        return ratio * 0.8
    # Also check if first 3 chars match (common typo pattern: right start, wrong end)
    if len(query_word) >= 3 and len(target_word) >= 3 and query_word[:3] == target_word[:3]:
        return 0.5
    return 0.0
