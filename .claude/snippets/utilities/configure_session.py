# From: session_manager.py:120
# Find/launch the browser window for a session.

    def configure_session(self, session_id: str) -> bool:
        """Find/launch the browser window for a session."""
        session = self._sessions.get(session_id)
        if not session or not session.client:
            return False

        ok = session.client.configure()
        if ok:
            session.hwnd = session.client.hwnd
            session.is_configured = True
            logger.info("Session %s configured: hwnd=%s", session_id, session.hwnd)
        return ok
