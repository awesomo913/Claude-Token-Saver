# From: ai_profiles.py:211
# Get a profile by name. Falls back to Custom if not found.

def get_profile(name: str) -> AIProfile:
    """Get a profile by name. Falls back to Custom if not found."""
    if name in PRESET_PROFILES:
        return PRESET_PROFILES[name]
    for p in load_custom_profiles():
        if p.name == name:
            return p
    return CUSTOM_PROFILE
