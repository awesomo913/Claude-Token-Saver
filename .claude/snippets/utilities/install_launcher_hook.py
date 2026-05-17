# From: claude_backend/auto_inject.py:367
# Install the launcher hook. Deduplicates existing launcher hooks first.

def install_launcher_hook() -> tuple[bool, str]:
    """Install the launcher hook. Deduplicates existing launcher hooks first."""
    return _install_hook(
        HOOK_ID_LAUNCH,
        HOOK_DESC_LAUNCH,
        _build_launcher_command(),
        _LAUNCH_LEGACY_SUBSTR,
    )
