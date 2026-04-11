# From: browser_actions.py:344
# Phase 1: Focus window, click input, paste prompt, send. ~3-5 seconds of mouse use.

def send_prompt_phase(hwnd: int, prompt: str, profile: AIProfile = GEMINI_PROFILE) -> None:
    """Phase 1: Focus window, click input, paste prompt, send. ~3-5 seconds of mouse use."""
    if not focus_window(hwnd):
        raise RuntimeError(f"Could not focus {profile.name} window")

    if not click_chat_input(hwnd, profile):
        raise RuntimeError(f"Could not click {profile.name} chat input")

    type_prompt(prompt)
    send_message(hwnd, profile)
    logger.info("Prompt sent to %s (%d chars)", profile.name, len(prompt))
