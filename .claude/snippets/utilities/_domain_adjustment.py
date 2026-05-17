# From: classifier/classifier.py:153
# Adjust score based on domain detection. Positive = toward Claude.

    def _domain_adjustment(self, text: str) -> float:
        """Adjust score based on domain detection. Positive = toward Claude."""
        adj = 0.0
        for _domain, info in self._keywords.get("domain_modifiers", {}).items():
            keywords = info.get("keywords", [])
            if any(kw in text for kw in keywords):
                strength = info.get("strength", 0.1)
                if info.get("bias") == "claude":
                    adj += strength
                else:
                    adj -= strength
        return adj
