# From: claude_backend/auto_inject.py:388
# Status of the UserPromptSubmit launcher hook.

def check_prompt_status() -> dict:
    """Status of the UserPromptSubmit launcher hook."""
    return _check_hook(
        HOOK_ID_PROMPT, _LAUNCH_LEGACY_SUBSTR, event="UserPromptSubmit",
    )
