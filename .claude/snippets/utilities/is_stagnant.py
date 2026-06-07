# From: NeoAutocoder/session.py:38
# Detect if code stopped evolving.

    def is_stagnant(self, threshold: int = 3) -> bool:
        """Detect if code stopped evolving."""
        if len(self.hash_history) < threshold:
            return False
        recent = self.hash_history[-threshold:]
        return len(set(recent)) == 1  # all identical
