# From: universal_client.py:511

class BrowserGeminiClient(UniversalBrowserClient):
    """Legacy alias — creates a UniversalBrowserClient with Gemini preset."""
    def __init__(self, **kwargs):
        profile = kwargs.pop("ai_profile", GEMINI_PROFILE)
        super().__init__(ai_profile=profile, **kwargs)
