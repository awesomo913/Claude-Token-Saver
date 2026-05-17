# From: claude_backend/search.py:288
# Cheap suffix-stripping stemmer. Not perfect, just good enough.

def _stem(word: str) -> str:
    """Cheap suffix-stripping stemmer. Not perfect, just good enough."""
    w = word.lower().strip()
    if len(w) <= 3:
        return w
    for suf in _SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            return w[:-len(suf)]
    return w
