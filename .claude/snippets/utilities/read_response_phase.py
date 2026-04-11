# From: browser_actions.py:400
# Phase 3: Focus window and read the response. ~3-5 seconds of mouse use.

def read_response_phase(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> str:
    """Phase 3: Focus window and read the response. ~3-5 seconds of mouse use."""
    logger.info("Reading %s response...", profile.name)
    raw = read_page_text_once(hwnd, profile)

    if not raw:
        raise RuntimeError(f"No response text could be read from {profile.name}")

    response = _extract_ai_response(raw, profile)
    logger.info("%s response: %d chars (raw: %d)", profile.name, len(response), len(raw))
    return response
