# From: cdp_client.py:609
# Check if Chrome is running with remote debugging enabled.

def is_cdp_available(port: int = DEFAULT_CDP_PORT) -> bool:
    """Check if Chrome is running with remote debugging enabled."""
    try:
        targets = discover_cdp_targets(port)
        return len(targets) > 0
    except Exception:
        return False
