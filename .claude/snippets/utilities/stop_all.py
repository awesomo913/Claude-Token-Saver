# From: session_manager.py:175
# Emergency stop all sessions.

    def stop_all(self) -> None:
        """Emergency stop all sessions."""
        for session in self._sessions.values():
            if session.executor and session.executor.is_running:
                session.executor.stop()
            if session.client:
                session.client.cancel()
        logger.info("All sessions stopped")
