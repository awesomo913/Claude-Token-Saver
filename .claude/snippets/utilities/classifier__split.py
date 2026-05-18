# From: classifier/splitter.py:21
# Decompose prompt into routed subtasks and build two output prompts.

    def split(
        self, prompt: str, classification: TaskClassification
    ) -> RoutingResult:
        """Decompose prompt into routed subtasks and build two output prompts."""

        if classification.routing == "free":
            return self._all_free(prompt)
        if classification.routing == "claude":
            return self._all_claude(prompt)

        # Split mode
        sentences = self._split_sentences(prompt)
        subtasks = self._classify_sentences(sentences)
        subtasks = self._merge_consecutive(subtasks)

        free_prompt = self._build_free_prompt(subtasks)
        claude_prompt = self._build_claude_prompt(subtasks, prompt)

        free_tokens = _estimate_tokens(free_prompt)
        claude_tokens = _estimate_tokens(claude_prompt)
        original_tokens = _estimate_tokens(prompt)
        savings = max(0.0, 1.0 - (claude_tokens / max(1, original_tokens)))

        return RoutingResult(
            original_prompt=prompt,
            subtasks=subtasks,
            free_prompt=free_prompt,
            claude_prompt=claude_prompt,
            free_token_estimate=free_tokens,
            claude_token_estimate=claude_tokens,
            savings_pct=round(savings, 3),
        )
