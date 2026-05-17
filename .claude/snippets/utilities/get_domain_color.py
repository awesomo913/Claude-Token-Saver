# From: claude_backend/search.py:90
# Get the badge color for a domain.

def get_domain_color(domain: str) -> str:
    """Get the badge color for a domain."""
    return DOMAIN_COLORS.get(domain, "#808080")
