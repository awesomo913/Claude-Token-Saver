# From: claude_backend/tokenizer.py:35
# Count tokens accurately with BPE, fallback to heuristic.

def count_tokens(text: str) -> int:
    """Count tokens accurately with BPE, fallback to heuristic.

    Returns token count. Never raises.
    """
    if not text:
        return 0
    enc = _get_encoder()
    if enc is not None:
        try:
            return len(enc.encode(text, disallowed_special=()))
        except Exception:
            pass
    # Fallback: chars * 10 / 32 (~3.2 chars per token)
    return len(text) * 10 // 32
