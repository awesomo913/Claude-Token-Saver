# From: cdp_client.py:555
# Query Chrome's /json endpoint to find all debuggable tabs.

def discover_cdp_targets(port: int = DEFAULT_CDP_PORT, host: str = "127.0.0.1") -> list[CDPTarget]:
    """Query Chrome's /json endpoint to find all debuggable tabs."""
    if not URLLIB_AVAILABLE:
        return []

    try:
        url = f"http://{host}:{port}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())

        targets = []
        for item in data:
            if item.get("type") != "page":
                continue
            ws_url = item.get("webSocketDebuggerUrl", "")
            if not ws_url:
                continue
            targets.append(CDPTarget(
                target_id=item.get("id", ""),
                title=item.get("title", ""),
                url=item.get("url", ""),
                ws_url=ws_url,
                tab_type=item.get("type", "page"),
            ))

        logger.debug("Found %d CDP targets on port %d", len(targets), port)
        return targets

    except Exception as e:
        logger.debug("CDP discovery failed on port %d: %s", port, e)
        return []
