# From: cdp_client.py:171
# Get CDP selectors for a given AI profile name.

def get_selectors_for_profile(profile_name: str) -> CDPSelectors:
    """Get CDP selectors for a given AI profile name."""
    return SELECTOR_PRESETS.get(profile_name, CDPSelectors())
