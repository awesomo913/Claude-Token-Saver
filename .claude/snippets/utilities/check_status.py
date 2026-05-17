# From: claude_backend/auto_inject.py:343
# Status of the prep hook.

def check_status() -> dict:
    """Status of the prep hook."""
    return _check_hook(HOOK_ID, _PREP_LEGACY_SUBSTR)
