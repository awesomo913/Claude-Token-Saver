# From: gemini_coder/task_manager.py:91
# Mark a task as completed.

    def complete(self, task: CodingTask) -> None:
        """Mark a task as completed."""
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        self._completed.append(task)
        self._notify_change()
