# From: claude_backend/http_server.py:598
# Check whether 127.0.0.1:port is free for bind.

def is_port_free(port: int) -> bool:
    """Check whether 127.0.0.1:port is free for bind.

    NOTE: unreliable on Windows when the running server has
    SO_REUSEADDR set (which `http.server.HTTPServer` does by default —
    `allow_reuse_address = 1`). A fresh bind from a different process
    can succeed even though the port is bound. Prefer `is_backend_alive`
    for "is OUR HTTP server up?" questions. Kept here for callers that
    actually need pre-bind availability (e.g. start_server).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False
    finally:
        try:
            s.close()
        except OSError:
            pass
