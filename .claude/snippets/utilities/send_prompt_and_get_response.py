# From: browser_actions.py:413
# Full cycle: send -> wait -> read. Used when NOT using traffic controller.

def send_prompt_and_get_response(
    hwnd: int,
    prompt: str,
    profile: AIProfile = GEMINI_PROFILE,
    timeout: float = MAX_GENERATE_WAIT,
    on_progress: Optional[callable] = None,
    cancel_event=None,
) -> str:
    """Full cycle: send -> wait -> read. Used when NOT using traffic controller.
    For traffic-controlled sessions, use the 3-phase API instead.
    """
    send_prompt_phase(hwnd, prompt, profile)

    wait_for_generation_done(
        hwnd, prompt_length=len(prompt), profile=profile,
        timeout=timeout, on_progress=on_progress,
        cancel_event=cancel_event,
    )

    time.sleep(POST_GENERATE_WAIT)
    return read_response_phase(hwnd, profile)
