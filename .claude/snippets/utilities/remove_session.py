# From: session_manager.py:156
# Remove a session completely.

    def remove_session(self, session_id: str) -> bool:
        """Remove a session completely."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.executor and session.executor.is_running:
            session.executor.stop()

        if session.client:
            session.client.cancel()
            session.client.release_hwnd()

        self._corner_map.pop(session.corner, None)
        del self._sessions[session_id]

        logger.info("Removed session %s: %s", session_id, session.display_name)
        return True
