# From: gemini_coder/task_manager.py:76
# Add a task to the queue.

    def add(self, task: CodingTask) -> None:
        """Add a task to the queue."""
        self._pending.append(task)
        self._notify_change()
