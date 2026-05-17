# From: claude_backend/auto_inject.py:395
# Install the UserPromptSubmit launcher. Dedupes existing first.

def install_prompt_hook() -> tuple[bool, str]:
    """Install the UserPromptSubmit launcher. Dedupes existing first."""
    return _install_hook(
        HOOK_ID_PROMPT,
        HOOK_DESC_PROMPT,
        _build_launcher_command(),
        _LAUNCH_LEGACY_SUBSTR,
        event="UserPromptSubmit",
    )
