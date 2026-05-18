# From: broadcast.py:289
# Stop all broadcast loops.

    def stop(self) -> None:
        """Stop all broadcast loops."""
        self._stop_event.set()
        self._running = False

        # Stop all session executors
        for session in self._sm.sessions:
            if session.client:
                session.client.cancel()

        logger.info("Broadcast stopped")
        if self._on_complete:
            self._on_complete(dict(self._iteration_counts))
