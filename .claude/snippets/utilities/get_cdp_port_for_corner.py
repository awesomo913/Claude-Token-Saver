# From: cdp_client.py:55
# Get the CDP port assigned to a screen corner.

def get_cdp_port_for_corner(corner: str) -> int:
    """Get the CDP port assigned to a screen corner."""
    return CDP_CORNER_PORTS.get(corner, DEFAULT_CDP_PORT)
