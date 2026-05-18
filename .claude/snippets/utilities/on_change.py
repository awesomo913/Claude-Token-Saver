# From: gemini_coder/task_manager.py:111
# Register a change callback.

    def on_change(self, callback: Callable) -> None:
        """Register a change callback."""
        self._on_change = callback
