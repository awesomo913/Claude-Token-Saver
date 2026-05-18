# From: gemini_coder/task_manager.py:119
# Clear all tasks.

    def clear(self) -> None:
        """Clear all tasks."""
        self._pending.clear()
        self._completed.clear()
        self._notify_change()
