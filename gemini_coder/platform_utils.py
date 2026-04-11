"""Platform utilities for cross-platform support."""

import os
import sys
from pathlib import Path
from typing import Literal


def detect_platform() -> Literal["windows", "macos", "linux"]:
    """Detect the current platform."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


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


def get_platform_name() -> str:
    """Return a human-readable platform name."""
    return detect_platform()
