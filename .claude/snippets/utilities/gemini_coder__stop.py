# From: gemini_coder/task_manager.py:173
# Stop executing tasks.

    def stop(self) -> None:
        """Stop executing tasks."""
        self._running = False
        if self._stop_event:
            self._stop_event.set()
