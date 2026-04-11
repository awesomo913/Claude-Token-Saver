# From: ai_profiles.py:228
# Save a custom profile to disk.

def save_custom_profile(profile: AIProfile) -> None:
    """Save a custom profile to disk."""
    path = _custom_profiles_path()
    profiles = load_custom_profiles()

    # Replace existing with same name, or add new
    found = False
    for i, p in enumerate(profiles):
        if p.name == profile.name:
            profiles[i] = profile
            found = True
            break
    if not found:
        profiles.append(profile)

    try:
        data = [p.to_dict() for p in profiles]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved custom profile: %s", profile.name)
    except Exception as e:
        logger.error("Failed to save custom profile: %s", e)
