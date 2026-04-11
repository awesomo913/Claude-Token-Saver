# From: browser_actions.py:357
# Extract just the AI response from full page text.

def _extract_ai_response(text: str, profile: AIProfile) -> str:
    """Extract just the AI response from full page text.

    When we Ctrl+A the page, we get nav bars, sidebars, buttons, etc.
    This tries to extract just the last meaningful response.
    """
    if not text:
        return ""

    lines = text.split('\n')

    # Filter out very short lines (buttons, nav items) and UI noise
    meaningful = []
    capture = False
    for line in lines:
        stripped = line.strip()
        # Skip empty lines at the start
        if not capture and not stripped:
            continue
        # Skip common UI noise
        if stripped in ("", "Send", "Copy", "Share", "Like", "Dislike",
                       "Create Artifact...", "Create image", "Create music",
                       "Create video", "Do tasks for me", "Boost my day",
                       "Help me learn", "Start a new message...",
                       "Send a message (/? for help)"):
            continue
        if len(stripped) < 3:
            continue
        # Once we find a substantial line, start capturing
        if len(stripped) > 20:
            capture = True
        if capture:
            meaningful.append(line)

    result = '\n'.join(meaningful).strip()

    # If we filtered too aggressively, return original
    if len(result) < 50 and len(text) > 100:
        return text.strip()

    return result
