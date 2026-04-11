# From: browser_actions.py:151
# Wait for the AI to finish generating.

def wait_for_generation_done(
    hwnd: int,
    prompt_length: int = 100,
    profile: AIProfile = GEMINI_PROFILE,
    timeout: float = MAX_GENERATE_WAIT,
    on_progress: Optional[callable] = None,
    cancel_event=None,
) -> None:
    """Wait for the AI to finish generating.

    Simple timed wait scaled by prompt length and profile.wait_multiplier.
    ZERO keyboard/mouse interaction during the entire wait.
    If cancel_event is set, raises InterruptedError immediately.
    """
    if prompt_length < 200:
        base = BASE_WAITS["short"]
    elif prompt_length < 1000:
        base = BASE_WAITS["medium"]
    elif prompt_length < 3000:
        base = BASE_WAITS["long"]
    else:
        base = BASE_WAITS["very_long"]

    wait_time = min(base * profile.wait_multiplier, timeout)

    logger.info("Waiting %.0fs for %s to generate (prompt=%d chars, multiplier=%.1f)...",
                wait_time, profile.name, prompt_length, profile.wait_multiplier)

    elapsed = 0
    while elapsed < wait_time:
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Cancelled during wait")
        chunk = min(2, wait_time - elapsed)
        time.sleep(chunk)
        elapsed += chunk
        if on_progress:
            remaining = int(wait_time - elapsed)
            on_progress(f"Waiting for {profile.name}... {remaining}s remaining")
