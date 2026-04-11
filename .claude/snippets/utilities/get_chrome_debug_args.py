# From: cdp_client.py:909
# Return Chrome command-line args needed for CDP debugging.

def get_chrome_debug_args(port: int = DEFAULT_CDP_PORT) -> list[str]:
    """Return Chrome command-line args needed for CDP debugging."""
    return [
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
