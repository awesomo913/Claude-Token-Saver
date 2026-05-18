# From: gemini_coder/platform_utils.py:9
# Detect the current platform.

def detect_platform() -> Literal["windows", "macos", "linux"]:
    """Detect the current platform."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"
