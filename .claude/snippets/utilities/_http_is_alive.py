# From: claude_backend/session_launcher.py:63
# Return True if the Token Saver HTTP server responds on localhost.

def _http_is_alive(port: int = _HTTP_PORT, timeout: float = 1.0) -> bool:
    """Return True if the Token Saver HTTP server responds on localhost."""
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{port}/projects", timeout=timeout
        )
        return True
    except Exception:
        return False
