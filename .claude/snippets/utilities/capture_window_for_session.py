# From: session_manager.py:184
# Assign a specific window handle to a session (from capture mode).

    def capture_window_for_session(self, session_id: str, hwnd: int) -> bool:
        """Assign a specific window handle to a session (from capture mode)."""
        session = self._sessions.get(session_id)
        if not session or not session.client:
            return False

        ok = session.client.configure_with_hwnd(hwnd)
        if ok:
            session.hwnd = hwnd
            session.is_configured = True
            logger.info("Captured hwnd=%d for session %s", hwnd, session_id)
        return ok
