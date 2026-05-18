# From: gemini_coder/task_manager.py:129

    def __init__(self, client, task_queue: TaskQueue) -> None:
        self._client = client
        self._queue = task_queue
        self._running = False
        self._stop_event = None
        self._thread = None
        self._callbacks = {}
