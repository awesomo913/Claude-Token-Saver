# From: gemini_coder/task_manager.py:81
# Get the next pending task.

    def next(self) -> Optional[CodingTask]:
        """Get the next pending task."""
        if self._pending:
            task = self._pending.pop(0)
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            self._notify_change()
            return task
        return None
