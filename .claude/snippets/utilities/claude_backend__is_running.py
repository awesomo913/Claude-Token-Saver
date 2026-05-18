# From: claude_backend/http_server.py:686
# Quick check whether server thread is alive.

def is_running() -> bool:
    """Quick check whether server thread is alive."""
    return _server_thread is not None and _server_thread.is_alive()
