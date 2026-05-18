# From: claude_backend/scanners/github.py:131
# Download file content as string.

def _download(url: str) -> Optional[str]:
    """Download file content as string."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, OSError) as e:
        logger.debug("Download failed %s: %s", url, e)
        return None
