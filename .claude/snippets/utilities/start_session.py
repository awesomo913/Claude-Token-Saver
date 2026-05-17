# From: session_manager.py:133
# Start executing the task queue for a session.

    def start_session(self, session_id: str) -> bool:
        """Start executing the task queue for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if not session.is_configured:
            if not self.configure_session(session_id):
                return False

        if session.executor and not session.executor.is_running:
            session.executor.start()
            logger.info("Session %s started: %s", session_id, session.display_name)
            return True
        return False
