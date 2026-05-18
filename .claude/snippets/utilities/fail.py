# From: gemini_coder/task_manager.py:98
# Mark a task as failed.

    def fail(self, task: CodingTask) -> None:
        """Mark a task as failed."""
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        self._completed.append(task)
        self._notify_change()
