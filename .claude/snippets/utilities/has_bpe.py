# From: claude_backend/tokenizer.py:52
# Check if real BPE tokenizer is available.

def has_bpe() -> bool:
    """Check if real BPE tokenizer is available."""
    return _get_encoder() is not None
