# From: gemini_coder/task_manager.py:126

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
