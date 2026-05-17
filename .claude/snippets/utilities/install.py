# From: claude_backend/auto_inject.py:348
# Install the prep hook. Deduplicates existing prep hooks first.

def install() -> tuple[bool, str]:
    """Install the prep hook. Deduplicates existing prep hooks first."""
    return _install_hook(
        HOOK_ID, HOOK_DESCRIPTION, _build_prep_command(), _PREP_LEGACY_SUBSTR,
    )
