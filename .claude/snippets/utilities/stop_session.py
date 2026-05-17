# From: session_manager.py:149
# Stop a session's task executor.

    def stop_session(self, session_id: str) -> None:
        """Stop a session's task executor."""
        session = self._sessions.get(session_id)
        if session and session.executor:
            session.executor.stop()
            logger.info("Session %s stopped", session_id)
