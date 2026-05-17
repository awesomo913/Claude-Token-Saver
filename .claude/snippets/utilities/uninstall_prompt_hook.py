# From: claude_backend/auto_inject.py:406
# Remove the UserPromptSubmit launcher hook.

def uninstall_prompt_hook() -> tuple[bool, str]:
    """Remove the UserPromptSubmit launcher hook."""
    return _uninstall_hook(
        HOOK_ID_PROMPT, _LAUNCH_LEGACY_SUBSTR, event="UserPromptSubmit",
    )
