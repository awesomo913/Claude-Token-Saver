# From: claude_backend/scanners/github.py:117
# Fetch JSON from a URL with optional auth token.

def _fetch_json(url: str, token: Optional[str] = None) -> object:
    """Fetch JSON from a URL with optional auth token."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "claude-token-saver")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError, OSError) as e:
        logger.debug("GitHub API error for %s: %s", url, e)
        return None
