# From: claude_backend/session_launcher.py:113
# Poll HTTP server in a background thread and log when it comes up (or times out).

def _verify_http_in_background(timeout_s: float = 10.0) -> None:
    """Poll HTTP server in a background thread and log when it comes up (or times out)."""
    def _poll() -> None:
        import time
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if _http_is_alive():
                _log_session("session_launcher: http=up (verified after spawn)")
                return
            time.sleep(1.5)
        _log_session("session_launcher: http=down after spawn (server did not respond within 10s)")
    threading.Thread(target=_poll, daemon=True, name="ts_http_verify").start()
