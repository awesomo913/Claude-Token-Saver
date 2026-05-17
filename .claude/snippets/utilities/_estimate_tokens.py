# From: classifier/splitter.py:10
# Rough token estimate: ~4 chars per token for English.

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)
