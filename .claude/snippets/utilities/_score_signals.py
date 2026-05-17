# From: classifier/classifier.py:135
# Score keyword matches for a signal group.

    def _score_signals(
        self, text: str, signal_group: str
    ) -> tuple[float, list[str]]:
        """Score keyword matches for a signal group."""
        groups = self._keywords.get(signal_group, {})
        total = 0.0
        matched_types: list[str] = []

        for category, info in groups.items():
            keywords = info.get("keywords", [])
            weight = info.get("weight", 1.0)
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                total += weight * min(hits, 3)  # cap per-category contribution
                matched_types.append(category)

        return total, matched_types
