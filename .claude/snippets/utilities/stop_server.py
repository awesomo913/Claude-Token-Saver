# From: claude_backend/http_server.py:673
# Shut down the running server. Mostly for tests / Quit.

def stop_server() -> None:
    """Shut down the running server. Mostly for tests / Quit."""
    global _server, _server_thread
    if _server is not None:
        try:
            _server.shutdown()
            _server.server_close()
        except Exception as e:
            logger.debug("Server shutdown error: %s", e)
    _server = None
    _server_thread = None
