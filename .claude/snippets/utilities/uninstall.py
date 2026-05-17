# From: claude_backend/auto_inject.py:355
# Remove the prep hook.

def uninstall() -> tuple[bool, str]:
    """Remove the prep hook."""
    return _uninstall_hook(HOOK_ID, _PREP_LEGACY_SUBSTR)
