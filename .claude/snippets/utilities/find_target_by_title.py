# From: cdp_client.py:599
# Find a CDP target whose title contains the given pattern.

def find_target_by_title(title_pattern: str, port: int = DEFAULT_CDP_PORT) -> Optional[CDPTarget]:
    """Find a CDP target whose title contains the given pattern."""
    targets = discover_cdp_targets(port)
    pattern_lower = title_pattern.lower()
    for target in targets:
        if pattern_lower in target.title.lower():
            return target
    return None
