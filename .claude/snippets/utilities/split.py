# From: smart_router.py:43
# Break prompt into free_prompt + claude_prompt.

    def split(self, prompt: str, cls: "TaskClassification") -> "RoutingResult":
        """Break prompt into free_prompt + claude_prompt."""
        return self._splitter.split(prompt, cls)
