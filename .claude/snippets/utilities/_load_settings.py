# From: claude_backend/auto_inject.py:145
# Load + parse settings.json. Returns (data, error_msg).

def _load_settings() -> tuple[dict | None, str]:
    """Load + parse settings.json. Returns (data, error_msg)."""
    if not SETTINGS_PATH.is_file():
        return None, f"settings.json not found at {SETTINGS_PATH}"
    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"Cannot read settings.json: {e}"
    try:
        return json.loads(text), ""
    except json.JSONDecodeError as e:
        return None, f"settings.json is not valid JSON: {e}"
