# From: claude_backend/http_server.py:623
# Authoritative check: is OUR HTTP backend answering on port?

def is_backend_alive(port: int, timeout: float = 0.4) -> bool:
    """Authoritative check: is OUR HTTP backend answering on port?

    Hits GET /health, returns True iff response body has `ok: true`.
    Independent of bind semantics, so it works correctly even on
    Windows where `is_port_free` lies due to SO_REUSEADDR.
    """
    import json as _json
    import urllib.error
    import urllib.request

    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return False
            body = _json.loads(r.read().decode("utf-8"))
            return bool(body.get("ok"))
    except (urllib.error.URLError, OSError, ValueError):
        return False
