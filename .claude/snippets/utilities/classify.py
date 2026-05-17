# From: smart_router.py:39
# Score the prompt and decide routing.

    def classify(self, prompt: str) -> "TaskClassification":
        """Score the prompt and decide routing."""
        return self._classifier.classify(prompt)
