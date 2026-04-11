"""Task management for Gemini Coder."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CodingTask:
    """A coding task to be executed by an AI agent."""
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    output_code: Optional[str] = None
    elapsed_seconds: float = 0.0
    time_budget_seconds: float = 180.0
    progress_fraction: float = 0.0
    iterations_completed: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    session_id: str = ""

    @property
    def is_complete(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "output_code": self.output_code,
            "elapsed_seconds": self.elapsed_seconds,
            "time_budget_seconds": self.time_budget_seconds,
            "iterations_completed": self.iterations_completed,
            "created_at": self.created_at,
            "task_id": self.task_id,
        }


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


class TaskExecutor:
    """Executes tasks from a queue using a client."""

    def __init__(self, client, task_queue: TaskQueue) -> None:
        self._client = client
        self._queue = task_queue
        self._running = False
        self._stop_event = None
        self._thread = None
        self._callbacks = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def set_callbacks(
        self,
        on_output: Optional[Callable] = None,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_tick: Optional[Callable] = None,
        on_status: Optional[Callable] = None,
    ) -> None:
        self._callbacks = {
            "on_output": on_output,
            "on_task_start": on_task_start,
            "on_task_complete": on_task_complete,
            "on_tick": on_tick,
            "on_status": on_status,
        }

    def _emit(self, key: str, *args):
        cb = self._callbacks.get(key)
        if cb:
            cb(*args)

    def start(self) -> None:
        """Start executing tasks from the queue."""
        if self._running:
            return
        self._running = True
        self._stop_event = __import__("threading").Event()

        import threading
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop executing tasks."""
        self._running = False
        if self._stop_event:
            self._stop_event.set()

    def _run_loop(self) -> None:
        """Main execution loop."""
        import threading

        while self._running and not self._stop_event.is_set():
            task = self._queue.next()
            if not task:
                break

            self._emit("on_task_start", task)
            self._emit("on_status", "working", f"Executing: {task.title}")

            try:
                start = time.time()
                
                result = self._client.generate(
                    prompt=task.description,
                    on_progress=lambda text: self._emit("on_output", "code", text),
                )

                task.output_code = result
                task.elapsed_seconds = time.time() - start
                self._queue.complete(task)

                self._emit("on_output", "result", result)
                self._emit("on_task_complete", task)

            except Exception as e:
                logger.error("Task execution failed: %s", e)
                task.elapsed_seconds = time.time() - (task.started_at or time.time())
                self._queue.fail(task)
                self._emit("on_output", "error", str(e))
                self._emit("on_task_complete", task)

            if self._stop_event and self._stop_event.is_set():
                break

        self._running = False
        self._emit("on_status", "idle", "Idle")
