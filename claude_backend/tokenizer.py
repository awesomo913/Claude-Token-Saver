"""Accurate token counting with BPE tokenizer + fast fallback.

Uses tiktoken (Rust-backed, millisecond speed) when available.
Falls back to chars * 10 / 32 heuristic if not installed.
Claude uses a different BPE vocabulary than GPT-4, so cl100k_base
is ~90% accurate for Claude (vs ~80% for the char heuristic).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_encoder = None
_loaded = False


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


def has_bpe() -> bool:
    """Check if real BPE tokenizer is available."""
    return _get_encoder() is not None
