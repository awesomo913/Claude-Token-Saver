# From: cdp_client.py:589
# Find a CDP target whose URL contains the given pattern.

def find_target_by_url(url_pattern: str, port: int = DEFAULT_CDP_PORT) -> Optional[CDPTarget]:
    """Find a CDP target whose URL contains the given pattern."""
    targets = discover_cdp_targets(port)
    pattern_lower = url_pattern.lower()
    for target in targets:
        if pattern_lower in target.url.lower():
            return target
    return None
