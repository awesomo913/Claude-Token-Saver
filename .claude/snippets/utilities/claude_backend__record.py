# From: claude_backend/tracker.py:59
# Record a token-saving event.

    def record(
        self,
        operation: str,
        tokens: int,
        project: str = "",
        detail: str = "",
        tokens_avoided: int = 0,
    ) -> None:
        """Record a token-saving event.

        Args:
            tokens: tokens actually provided/referenced (the cost)
            tokens_avoided: tokens Claude would have read without the tool (the savings)
        Operations: "clipboard_copy", "bootstrap", "prep", "context_build"
        """
        self._append({
            "ts": _now(),
            "op": operation,
            "tokens": tokens,
            "tokens_avoided": tokens_avoided,
            "project": project,
            "detail": detail,
        })
