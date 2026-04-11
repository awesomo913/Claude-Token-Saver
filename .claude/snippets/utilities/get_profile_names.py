# From: ai_profiles.py:202
# Get all available profile names (presets + saved custom).

def get_profile_names() -> list[str]:
    """Get all available profile names (presets + saved custom)."""
    names = list(PRESET_PROFILES.keys())
    for p in load_custom_profiles():
        if p.name not in names:
            names.append(p.name)
    return names
