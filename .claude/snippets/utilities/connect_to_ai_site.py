# From: cdp_client.py:1003
# Find a browser tab matching the AI site and return a chat automation object.

def connect_to_ai_site(
    profile_name: str,
    url_pattern: str = "",
    title_pattern: str = "",
    port: int = DEFAULT_CDP_PORT,
) -> Optional[CDPChatAutomation]:
    """Find a browser tab matching the AI site and return a chat automation object.

    Tries the specified port first, then scans all corner ports.

    Args:
        profile_name: Name of the AI profile (e.g., "Gemini", "ChatGPT")
        url_pattern: URL substring to match (e.g., "gemini.google.com")
        title_pattern: Window title substring to match
        port: CDP debugging port (tries this first, then others)

    Returns:
        CDPChatAutomation ready to use, or None if not found.
    """
    # Build list of ports to try: specified port first, then all corner ports
    ports_to_try = [port]
    for p in CDP_CORNER_PORTS.values():
        if p not in ports_to_try:
            ports_to_try.append(p)

    for try_port in ports_to_try:
        target = None
        if url_pattern:
            target = find_target_by_url(url_pattern, try_port)
        if not target and title_pattern:
            target = find_target_by_title(title_pattern, try_port)

        if target:
            conn = CDPConnection(target.ws_url)
            if conn.connect():
                selectors = get_selectors_for_profile(profile_name)
                logger.info("CDP connected to %s on port %d", profile_name, try_port)
                return CDPChatAutomation(conn, selectors, profile_name)

    logger.warning("No CDP target found for %s (url=%s, title=%s) on any port",
                    profile_name, url_pattern, title_pattern)
    return None
