# From: claude_backend/prompt_builder.py:65
# Detect what the user is trying to do from their request text.

def detect_intent(request: str) -> str:
    """Detect what the user is trying to do from their request text."""
    lower = request.lower()
    scores: dict[str, int] = {}
    for intent, keywords in _INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "code"
