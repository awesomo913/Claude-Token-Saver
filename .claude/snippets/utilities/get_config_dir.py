# From: gemini_coder/platform_utils.py:19
# Get the config directory for this application.

def get_config_dir() -> Path:
    """Get the config directory for this application."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    
    config_dir = base / "gemini_coder"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
