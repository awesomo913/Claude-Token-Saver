# From: classifier/classifier.py:244

    @staticmethod
    def _build_reasoning(
        free_types: list[str],
        claude_types: list[str],
        complexity: float,
        structural: float,
        file_refs: int,
    ) -> str:
        parts: list[str] = []
        if free_types:
            parts.append(f"Free-model signals: {', '.join(free_types)}")
        if claude_types:
            parts.append(f"Claude signals: {', '.join(claude_types)}")
        parts.append(f"Complexity: {complexity:.2f}")
        if structural > 0.1:
            parts.append(f"Structural complexity: {structural:.2f}")
        if file_refs >= 2:
            parts.append(f"References {file_refs} files")
        return " | ".join(parts)
