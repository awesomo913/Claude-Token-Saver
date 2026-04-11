"""Theme and styling for Gemini Coder UI."""

from typing import Dict

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

ICONS = {
    "play": "\u25B6",
    "stop": "\u25A0",
    "check": "\u2713",
    "gear": "\u2699",
    "tasks": "\u2630",
    "save": "\U0001F4BE",
    "folder": "\U0001F4C2",
}


def get_colors(theme: str = "dark") -> Dict[str, str]:
    """Get color scheme based on theme."""
    if theme == "dark":
        return {
            "bg_primary": "#1a1a1a",
            "bg_secondary": "#2d2d2d",
            "bg_tertiary": "#252525",
            "bg_card": "#212121",
            "bg_input": "#1e1e1e",
            "bg_hover": "#3d3d3d",
            "fg_primary": "#ffffff",
            "fg_secondary": "#b0b0b0",
            "fg_heading": "#ffffff",
            "fg_muted": "#808080",
            "border": "#404040",
            "accent": "#0078d4",
            "accent_hover": "#1084d8",
            "success": "#107c10",
            "warning": "#ff8c00",
            "error": "#e81123",
            "info": "#0078d4",
        }
    else:
        return {
            "bg_primary": "#f5f5f5",
            "bg_secondary": "#e0e0e0",
            "bg_tertiary": "#ffffff",
            "bg_card": "#ffffff",
            "bg_input": "#ffffff",
            "bg_hover": "#e8e8e8",
            "fg_primary": "#1a1a1a",
            "fg_secondary": "#666666",
            "fg_heading": "#1a1a1a",
            "fg_muted": "#999999",
            "border": "#cccccc",
            "accent": "#0078d4",
            "accent_hover": "#106ebe",
            "success": "#107c10",
            "warning": "#ff8c00",
            "error": "#e81123",
            "info": "#0078d4",
        }
