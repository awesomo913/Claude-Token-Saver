# From: smart_router.py:55
# Pick the first session running Claude.

    @staticmethod
    def find_claude_session(sessions: list) -> Optional[Any]:
        """Pick the first session running Claude."""
        for s in sessions:
            if s.ai_profile.name in CLAUDE_PROFILES and s.is_configured:
                return s
        return None
