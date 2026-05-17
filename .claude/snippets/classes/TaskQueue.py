# From: gemini_coder/task_manager.py:59

class TaskQueue:
    """Queue of tasks for a session."""

    def __init__(self, save_path: Optional[Path] = None) -> None:
        self._pending: list[CodingTask] = []
        self._completed: list[CodingTask] = []
        self._save_path = save_path
        self._on_change: Optional[Callable] = None

    @property
    def pending_tasks(self) -> list[CodingTask]:
        return list(self._pending)

    @property
    def completed_tasks(self) -> list[CodingTask]:
        return list(self._completed)

    def add(self, task: CodingTask) -> None:
        """Add a task to the queue."""
        self._pending.append(task)
        self._notify_change()

    def next(self) -> Optional[CodingTask]:
        """Get the next pending task."""
        if self._pending:
            task = self._pending.pop(0)
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            self._notify_change()
            return task
        return None

    def complete(self, task: CodingTask) -> None:
        """Mark a task as completed."""
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        self._completed.append(task)
        self._notify_change()

    def fail(self, task: CodingTask) -> None:
        """Mark a task as failed."""
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        self._completed.append(task)
        self._notify_change()

    def cancel(self, task: CodingTask) -> None:
        """Cancel a task."""
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        self._notify_change()

    def on_change(self, callback: Callable) -> None:
        """Register a change callback."""
        self._on_change = callback

    def _notify_change(self) -> None:
        if self._on_change:
            self._on_change()

    def clear(self) -> None:
        """Clear all tasks."""
        self._pending.clear()
        self._completed.clear()
        self._notify_change()
