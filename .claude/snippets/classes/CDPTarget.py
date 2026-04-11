# From: cdp_client.py:545

@dataclass
class CDPTarget:
    """A Chrome/Edge tab available for CDP connection."""
    target_id: str
    title: str
    url: str
    ws_url: str
    tab_type: str = "page"
