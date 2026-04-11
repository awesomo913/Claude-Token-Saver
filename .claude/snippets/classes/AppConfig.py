# From: gemini_coder/config.py:11

@dataclass
class AppConfig:
    """Application configuration."""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    auto_scroll: bool = True
    task_default_minutes: int = 3
    expand_depth_limit: int = 3
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.9
    auto_save_enabled: bool = True
