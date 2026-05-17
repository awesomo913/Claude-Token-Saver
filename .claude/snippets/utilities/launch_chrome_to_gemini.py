# From: window_manager.py:356
# Legacy: launch Chrome to Gemini.

def launch_chrome_to_gemini(
    url: str = "https://gemini.google.com/app",
    corner: str = "bottom-right",
) -> Optional[int]:
    """Legacy: launch Chrome to Gemini."""
    return launch_to_url(url, corner, browser="chrome", title_pattern="gemini")
