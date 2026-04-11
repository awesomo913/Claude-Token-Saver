# From: cdp_test.py:27
# Detect which AI site a URL belongs to.

def _detect_ai_site(url: str) -> str:
    """Detect which AI site a URL belongs to."""
    url_lower = url.lower()
    if "gemini.google.com" in url_lower:
        return "Gemini"
    if "chatgpt.com" in url_lower or "chat.openai.com" in url_lower:
        return "ChatGPT"
    if "claude.ai" in url_lower:
        return "Claude"
    if "openrouter.ai" in url_lower:
        return "OpenRouter"
    if "copilot.microsoft.com" in url_lower:
        return "Copilot"
    return ""
