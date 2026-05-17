# From: claude_backend/auto_inject.py:377
# Remove the launcher hook.

def uninstall_launcher_hook() -> tuple[bool, str]:
    """Remove the launcher hook."""
    return _uninstall_hook(HOOK_ID_LAUNCH, _LAUNCH_LEGACY_SUBSTR)
