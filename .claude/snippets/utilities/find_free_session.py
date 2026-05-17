# From: smart_router.py:47
# Pick the first session running a free AI profile.

    @staticmethod
    def find_free_session(sessions: list) -> Optional[Any]:
        """Pick the first session running a free AI profile."""
        for s in sessions:
            if s.ai_profile.name in FREE_PROFILES and s.is_configured:
                return s
        return None
