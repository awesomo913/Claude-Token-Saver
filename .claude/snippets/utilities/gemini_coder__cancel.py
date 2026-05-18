# From: gemini_coder/task_manager.py:105
# Cancel a task.

    def cancel(self, task: CodingTask) -> None:
        """Cancel a task."""
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        self._notify_change()
