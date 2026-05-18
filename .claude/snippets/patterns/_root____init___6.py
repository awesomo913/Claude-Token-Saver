# From: universal_client.py:513

    def __init__(self, **kwargs):
        profile = kwargs.pop("ai_profile", GEMINI_PROFILE)
        super().__init__(ai_profile=profile, **kwargs)
