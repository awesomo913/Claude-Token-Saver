# From: claude_backend/tokenizer.py:19
# Load tiktoken encoder once (lazy singleton).

def _get_encoder():
    """Load tiktoken encoder once (lazy singleton)."""
    global _encoder, _loaded
    if _loaded:
        return _encoder
    _loaded = True
    try:
        import tiktoken
        _encoder = tiktoken.get_encoding("cl100k_base")
        logger.debug("tiktoken loaded (cl100k_base)")
    except Exception as e:
        logger.debug("tiktoken not available, using heuristic: %s", e)
        _encoder = None
    return _encoder
