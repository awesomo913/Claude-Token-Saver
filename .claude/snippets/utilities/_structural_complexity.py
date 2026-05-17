# From: classifier/classifier.py:174
# Heuristic scoring based on prompt structure (0.0–1.0).

    @staticmethod
    def _structural_complexity(prompt: str) -> float:
        """Heuristic scoring based on prompt structure (0.0–1.0)."""
        score = 0.0

        sentences = re.split(r"(?<=[.!?])\s+", prompt.strip())
        if len(sentences) > 8:
            score += 0.2

        word_count = len(prompt.split())
        if word_count > 300:
            score += 0.1

        # Conditional language
        conditionals = ["but", "however", "except when", "edge case", "unless",
                        "only if", "special case", "in some cases"]
        if any(c in prompt.lower() for c in conditionals):
            score += 0.15

        # Error / stack trace indicators
        error_signs = ["traceback", "error:", "exception", "at line", "failed with",
                       "stack trace", "segmentation fault", "panic:"]
        if any(e in prompt.lower() for e in error_signs):
            score += 0.3

        return min(1.0, score)
