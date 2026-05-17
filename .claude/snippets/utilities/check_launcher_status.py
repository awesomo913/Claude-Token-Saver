# From: claude_backend/auto_inject.py:362
# Status of the launcher hook.

def check_launcher_status() -> dict:
    """Status of the launcher hook."""
    return _check_hook(HOOK_ID_LAUNCH, _LAUNCH_LEGACY_SUBSTR)
