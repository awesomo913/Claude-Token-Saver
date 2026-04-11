"""AI profiles for universal browser automation.

Each AIProfile describes how to interact with a specific AI's web chat:
where the input box is, how to send, how long to wait, and how to find
the window. Preset profiles are provided for common AI services.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AIProfile:
    """Describes how to automate a specific AI web chat."""
    name: str = "Custom"
    title_pattern: str = ""             # Window title substring (case-insensitive)
    url_pattern: str = ""               # URL substring for CDP tab matching
    input_offset_from_bottom: int = 80  # Pixels from window bottom to input center
    send_method: str = "enter"          # "enter" or "click_button"
    send_button_right_offset: int = 60  # Pixels from right edge (for click_button)
    send_button_bottom_offset: int = 80 # Pixels from bottom (for click_button)
    wait_multiplier: float = 1.0        # Scales all wait times (1.0=normal, 2.0=double)
    read_click_fraction: float = 0.33   # Where to click before Ctrl+A (fraction from top)
    url: str = ""                       # URL to launch (empty = find existing window)
    browser: str = "any"                # "chrome", "edge", "firefox", "any"
    notes: str = ""                     # Help text about quirks

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AIProfile":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


# ── Preset profiles ───────────────────────────────────────────────

GEMINI_PROFILE = AIProfile(
    name="Gemini",
    title_pattern="gemini",
    url_pattern="gemini.google.com",
    input_offset_from_bottom=80,
    send_method="enter",
    wait_multiplier=1.0,
    read_click_fraction=0.33,
    url="https://gemini.google.com/app",
    browser="chrome",
    notes="Google's Gemini. Free tier, no API limits via browser.",
)

CHATGPT_PROFILE = AIProfile(
    name="ChatGPT",
    title_pattern="chatgpt",
    url_pattern="chatgpt.com",
    input_offset_from_bottom=85,
    send_method="enter",
    wait_multiplier=1.2,
    read_click_fraction=0.30,
    url="https://chatgpt.com",
    browser="chrome",
    notes="OpenAI ChatGPT. Enter sends by default. May need login.",
)

CLAUDE_PROFILE = AIProfile(
    name="Claude",
    title_pattern="claude",
    url_pattern="claude.ai",
    input_offset_from_bottom=90,
    send_method="enter",
    wait_multiplier=1.3,
    read_click_fraction=0.30,
    url="https://claude.ai/new",
    browser="chrome",
    notes="Anthropic Claude. Longer responses, slightly slower.",
)

OLLAMA_PROFILE = AIProfile(
    name="Ollama Web UI",
    title_pattern="open webui",
    url_pattern="localhost:3000",
    input_offset_from_bottom=75,
    send_method="enter",
    wait_multiplier=2.0,
    read_click_fraction=0.33,
    url="http://localhost:3000",
    browser="chrome",
    notes="Local Ollama with Open WebUI. Speed depends on hardware.",
)

LMSTUDIO_PROFILE = AIProfile(
    name="LM Studio",
    title_pattern="lm studio",
    input_offset_from_bottom=80,
    send_method="enter",
    wait_multiplier=2.5,
    read_click_fraction=0.33,
    url="",
    browser="any",
    notes="Local LM Studio app. Native window, not a browser.",
)

COPILOT_PROFILE = AIProfile(
    name="Copilot",
    title_pattern="copilot",
    url_pattern="copilot.microsoft.com",
    input_offset_from_bottom=85,
    send_method="enter",
    wait_multiplier=1.0,
    read_click_fraction=0.30,
    url="https://copilot.microsoft.com",
    browser="edge",
    notes="Microsoft Copilot. Works in Edge or Chrome.",
)

OPENROUTER_PROFILE = AIProfile(
    name="OpenRouter",
    title_pattern="openrouter",
    url_pattern="openrouter.ai",
    input_offset_from_bottom=55,
    send_method="click_button",
    send_button_right_offset=40,
    send_button_bottom_offset=50,
    wait_multiplier=1.2,
    read_click_fraction=0.40,
    url="https://openrouter.ai/playground",
    browser="chrome",
    notes="OpenRouter AI Playground. Supports multiple models. Multiple windows OK.",
)

# Best free models on OpenRouter ranked by coding quality.
# Used to auto-assign different models to different sessions.
OPENROUTER_FREE_MODELS = [
    "Qwen3.6 Plus Preview (free)",
    "Hermes 3 405B Instruct (free)",
    "DeepSeek V3 (free)",
    "DeepSeek R1 (free)",
    "Llama 4 Maverick (free)",
    "Llama 3.3 70B Instruct (free)",
    "Gemma 3 27B (free)",
    "Mistral Small 3.1 (free)",
    "Phi-4 Multimodal Instruct (free)",
]

TERMINAL_PROFILE = AIProfile(
    name="Terminal / PowerShell",
    title_pattern="powershell",
    input_offset_from_bottom=20,
    send_method="enter",
    wait_multiplier=2.0,
    read_click_fraction=0.50,
    url="",
    browser="any",
    notes="Terminal/PowerShell/CMD. Click anywhere to focus, paste, Enter.",
)

OLLAMA_TERMINAL_PROFILE = AIProfile(
    name="Ollama (Terminal)",
    title_pattern="ollama",
    input_offset_from_bottom=20,
    send_method="enter",
    wait_multiplier=1.5,
    read_click_fraction=0.50,
    url="",
    browser="any",
    notes="Ollama running in terminal. Paste prompt, Enter to send.",
)

CUSTOM_PROFILE = AIProfile(
    name="Custom",
    title_pattern="",
    input_offset_from_bottom=80,
    send_method="enter",
    wait_multiplier=1.0,
    read_click_fraction=0.33,
    url="",
    browser="any",
    notes="Custom profile. Set the title pattern to match your AI window.",
)

# Registry of all presets
PRESET_PROFILES: dict[str, AIProfile] = {
    "Gemini": GEMINI_PROFILE,
    "ChatGPT": CHATGPT_PROFILE,
    "Claude": CLAUDE_PROFILE,
    "Ollama Web UI": OLLAMA_PROFILE,
    "LM Studio": LMSTUDIO_PROFILE,
    "Copilot": COPILOT_PROFILE,
    "OpenRouter": OPENROUTER_PROFILE,
    "Terminal / PowerShell": TERMINAL_PROFILE,
    "Ollama (Terminal)": OLLAMA_TERMINAL_PROFILE,
    "Custom": CUSTOM_PROFILE,
}


def get_profile_names() -> list[str]:
    """Get all available profile names (presets + saved custom)."""
    names = list(PRESET_PROFILES.keys())
    for p in load_custom_profiles():
        if p.name not in names:
            names.append(p.name)
    return names


def get_profile(name: str) -> AIProfile:
    """Get a profile by name. Falls back to Custom if not found."""
    if name in PRESET_PROFILES:
        return PRESET_PROFILES[name]
    for p in load_custom_profiles():
        if p.name == name:
            return p
    return CUSTOM_PROFILE


# ── Custom profile persistence ────────────────────────────────────

def _custom_profiles_path() -> Path:
    from gemini_coder.platform_utils import get_config_dir
    return get_config_dir() / "ai_profiles_custom.json"


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


def load_custom_profiles() -> list[AIProfile]:
    """Load custom profiles from disk."""
    path = _custom_profiles_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [AIProfile.from_dict(d) for d in data]
    except Exception as e:
        logger.error("Failed to load custom profiles: %s", e)
        return []
