# From: gemini_coder/task_manager.py:162
# Start executing tasks from the queue.

    def start(self) -> None:
        """Start executing tasks from the queue."""
        if self._running:
            return
        self._running = True
        self._stop_event = __import__("threading").Event()

        import threading
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
