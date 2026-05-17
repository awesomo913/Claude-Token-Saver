# From: claude_backend/http_server.py:645
# Start HTTP server in a daemon thread. Idempotent.

def start_server(port: int) -> bool:
    """Start HTTP server in a daemon thread. Idempotent.

    Returns True on successful start (or already-running). False if port
    is unavailable or another error prevents binding.
    """
    global _server, _server_thread
    if _server is not None and _server_thread is not None and _server_thread.is_alive():
        return True

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    except OSError as e:
        logger.warning("HTTP server bind failed on 127.0.0.1:%d: %s", port, e)
        return False

    thread = threading.Thread(
        target=server.serve_forever,
        name="token_saver_http",
        daemon=True,
    )
    thread.start()
    _server = server
    _server_thread = thread
    logger.info("HTTP server listening on 127.0.0.1:%d", port)
    return True
