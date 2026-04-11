"""Low-level browser actions for controlling ANY AI web chat.

Parameterized by AIProfile — the same click/paste/Enter/read sequence
works for Gemini, ChatGPT, Claude, Ollama, LM Studio, or any AI chat.
The AIProfile tells us where the input is, how to send, and how long to wait.

DESIGN: Mouse/keyboard is used ONLY for sending (once) and reading (once at end).
During the wait period: ZERO keyboard/mouse interaction.
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Optional

from .ai_profiles import AIProfile, GEMINI_PROFILE

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Windows are at screen corners — failsafe triggers constantly
    pyautogui.PAUSE = 0.05
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

logger = logging.getLogger(__name__)

# Base wait times (seconds) — scaled by profile.wait_multiplier
BASE_WAITS = {
    "short": 15,    # < 200 chars
    "medium": 30,   # 200-1000 chars
    "long": 45,     # 1000-3000 chars
    "very_long": 60 # 3000+ chars
}
MAX_GENERATE_WAIT = 300
POST_GENERATE_WAIT = 3.0


# ── Win32 helpers (zero keyboard/mouse impact) ────────────────────

def _get_window_title(hwnd: int) -> str:
    """Read window title via Win32. Zero impact."""
    try:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""


def focus_window(hwnd: int) -> bool:
    """Bring a window to the foreground."""
    try:
        user32 = ctypes.windll.user32
        if not user32.IsWindow(hwnd):
            logger.error("Window %d no longer exists", hwnd)
            return False
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        logger.error("Failed to focus window %d: %s", hwnd, e)
        return False


def get_window_rect(hwnd: int) -> Optional[tuple[int, int, int, int]]:
    """Get window position (left, top, right, bottom)."""
    try:
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return None


# ── Sending prompts ───────────────────────────────────────────────

def click_chat_input(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> bool:
    """Click on the AI chat input area using profile offsets."""
    if not PYAUTOGUI_AVAILABLE:
        return False

    rect = get_window_rect(hwnd)
    if not rect:
        return False

    left, top, right, bottom = rect
    win_w = right - left

    # Chat input is usually center-right (sites have left sidebars)
    # Use 60% from left edge for the x-coordinate
    cx = left + int(win_w * 0.6)
    cy = bottom - profile.input_offset_from_bottom

    focus_window(hwnd)
    time.sleep(0.3)
    pyautogui.click(cx, cy)
    time.sleep(0.5)
    return True


def type_prompt(text: str, chunk_size: int = 500) -> None:
    """Type text into the focused input via clipboard paste."""
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return

    if len(text) <= chunk_size:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        return

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        pyperclip.copy(chunk)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.15)

    time.sleep(0.3)


def send_message(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> None:
    """Send the message using the profile's send method."""
    if not PYAUTOGUI_AVAILABLE:
        return

    if profile.send_method == "click_button":
        rect = get_window_rect(hwnd)
        if rect:
            left, top, right, bottom = rect
            sx = right - profile.send_button_right_offset
            sy = bottom - profile.send_button_bottom_offset
            pyautogui.click(sx, sy)
    else:
        pyautogui.press("enter")

    time.sleep(0.5)


# ── Waiting for response (ZERO keyboard/mouse) ───────────────────

def wait_for_generation_done(
    hwnd: int,
    prompt_length: int = 100,
    profile: AIProfile = GEMINI_PROFILE,
    timeout: float = MAX_GENERATE_WAIT,
    on_progress: Optional[callable] = None,
    cancel_event=None,
) -> None:
    """Wait for the AI to finish generating.

    Simple timed wait scaled by prompt length and profile.wait_multiplier.
    ZERO keyboard/mouse interaction during the entire wait.
    If cancel_event is set, raises InterruptedError immediately.
    """
    if prompt_length < 200:
        base = BASE_WAITS["short"]
    elif prompt_length < 1000:
        base = BASE_WAITS["medium"]
    elif prompt_length < 3000:
        base = BASE_WAITS["long"]
    else:
        base = BASE_WAITS["very_long"]

    wait_time = min(base * profile.wait_multiplier, timeout)

    logger.info("Waiting %.0fs for %s to generate (prompt=%d chars, multiplier=%.1f)...",
                wait_time, profile.name, prompt_length, profile.wait_multiplier)

    elapsed = 0
    while elapsed < wait_time:
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Cancelled during wait")
        chunk = min(2, wait_time - elapsed)
        time.sleep(chunk)
        elapsed += chunk
        if on_progress:
            remaining = int(wait_time - elapsed)
            on_progress(f"Waiting for {profile.name}... {remaining}s remaining")


# ── Reading response (done ONCE at the end) ───────────────────────

def _is_terminal_window(hwnd: int) -> bool:
    """Check if the window is a terminal (CMD, PowerShell, Windows Terminal)."""
    try:
        cls = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, cls, 256)
        terminal_classes = {"ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS",
                           "PseudoConsoleWindow", "mintty"}
        return cls.value in terminal_classes
    except Exception:
        return False


def read_page_text_once(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> str:
    """Read all visible text from the AI page or terminal. Done ONCE, carefully."""
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return ""

    try:
        rect = get_window_rect(hwnd)
        if not rect:
            return ""

        left, top, right, bottom = rect
        is_terminal = _is_terminal_window(hwnd)

        # Ensure THIS window is focused
        focus_window(hwnd)
        time.sleep(0.5)
        focus_window(hwnd)
        time.sleep(0.3)

        pyperclip.copy("__SENTINEL__")

        if is_terminal:
            # Terminals: right-click opens context menu with "Select All" / "Copy"
            # Or use keyboard: Ctrl+Shift+A to select all, then Enter to copy
            # Windows Terminal / PowerShell: Ctrl+A selects in input only
            # Best approach: click body area, then Ctrl+Shift+A, Enter
            safe_x = left + int((right - left) * 0.5)
            safe_y = top + int((bottom - top) * 0.5)
            pyautogui.click(safe_x, safe_y)
            time.sleep(0.3)

            # Select all text in terminal buffer
            pyautogui.hotkey("ctrl", "shift", "a")  # Windows Terminal: select all
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "shift", "c")  # Copy selection
            time.sleep(0.5)
        else:
            # Browser: click safe area, Ctrl+A, Ctrl+C
            safe_x = left + int((right - left) * 0.6)
            safe_y = top + int((bottom - top) * profile.read_click_fraction)
            pyautogui.click(safe_x, safe_y)
            time.sleep(0.5)

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.5)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.8)

        text = pyperclip.paste()

        # Clean up
        pyautogui.press("escape")
        time.sleep(0.1)
        pyperclip.copy("")
        time.sleep(0.1)

        if text == "__SENTINEL__" or not text:
            return ""

        return text.strip()

    except Exception as e:
        logger.error("Failed to read page text: %s", e)
        return ""


# ── Model switching (OpenRouter and similar) ─────────────────────

def switch_model_openrouter(hwnd: int, model_name: str) -> bool:
    """Switch the active model on OpenRouter's AI Chat Playground.

    OpenRouter layout: model tabs appear near the top of the chat pane.
    There's a "+" button to add a new model tab. Clicking "+" opens
    a model search dropdown. We type the model name, click the result.

    Also works if the model is already a tab — we just click it.
    """
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        return False

    try:
        rect = get_window_rect(hwnd)
        if not rect:
            return False

        left, top, right, bottom = rect
        win_w = right - left
        win_h = bottom - top
        focus_window(hwnd)
        time.sleep(0.5)

        # Check window title to see if model is already selected
        title = _get_window_title(hwnd)

        # OpenRouter chat layout:
        # - Top bar: OpenRouter logo + nav (~40px)
        # - Below that: model tabs row (~35px) with "+" button at the end
        # - Below that: chat area
        # The model tab row starts about 90-110px from top of window

        # Click the "+" button to open model picker
        # "+" is after the existing tabs, roughly right-center area
        plus_x = left + int(win_w * 0.45)
        plus_y = top + 105  # Model tab row area
        pyautogui.click(plus_x, plus_y)
        time.sleep(1.0)

        # A search/dropdown should appear — type model name to filter
        # Clear any existing text first
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)

        # Type the short search term (just key part of model name)
        # e.g., "Qwen3.6" from "Qwen3.6 Plus Preview (free)"
        search_term = model_name.split("(")[0].strip()  # Remove "(free)" etc.
        pyperclip.copy(search_term)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.5)

        # Click the first search result (appears below the search input)
        result_x = plus_x
        result_y = plus_y + 60
        pyautogui.click(result_x, result_y)
        time.sleep(0.8)

        # Press Escape to close any remaining dropdown
        pyautogui.press("escape")
        time.sleep(0.3)

        logger.info("Switched model to '%s' on hwnd=%d", model_name, hwnd)
        return True

    except Exception as e:
        logger.warning("Failed to switch model: %s", e)
        return False


# ── Main entry point ──────────────────────────────────────────────

def send_prompt_phase(hwnd: int, prompt: str, profile: AIProfile = GEMINI_PROFILE) -> None:
    """Phase 1: Focus window, click input, paste prompt, send. ~3-5 seconds of mouse use."""
    if not focus_window(hwnd):
        raise RuntimeError(f"Could not focus {profile.name} window")

    if not click_chat_input(hwnd, profile):
        raise RuntimeError(f"Could not click {profile.name} chat input")

    type_prompt(prompt)
    send_message(hwnd, profile)
    logger.info("Prompt sent to %s (%d chars)", profile.name, len(prompt))


def _extract_ai_response(text: str, profile: AIProfile) -> str:
    """Extract just the AI response from full page text.

    When we Ctrl+A the page, we get nav bars, sidebars, buttons, etc.
    This tries to extract just the last meaningful response.
    """
    if not text:
        return ""

    lines = text.split('\n')

    # Filter out very short lines (buttons, nav items) and UI noise
    meaningful = []
    capture = False
    for line in lines:
        stripped = line.strip()
        # Skip empty lines at the start
        if not capture and not stripped:
            continue
        # Skip common UI noise
        if stripped in ("", "Send", "Copy", "Share", "Like", "Dislike",
                       "Create Artifact...", "Create image", "Create music",
                       "Create video", "Do tasks for me", "Boost my day",
                       "Help me learn", "Start a new message...",
                       "Send a message (/? for help)"):
            continue
        if len(stripped) < 3:
            continue
        # Once we find a substantial line, start capturing
        if len(stripped) > 20:
            capture = True
        if capture:
            meaningful.append(line)

    result = '\n'.join(meaningful).strip()

    # If we filtered too aggressively, return original
    if len(result) < 50 and len(text) > 100:
        return text.strip()

    return result


def read_response_phase(hwnd: int, profile: AIProfile = GEMINI_PROFILE) -> str:
    """Phase 3: Focus window and read the response. ~3-5 seconds of mouse use."""
    logger.info("Reading %s response...", profile.name)
    raw = read_page_text_once(hwnd, profile)

    if not raw:
        raise RuntimeError(f"No response text could be read from {profile.name}")

    response = _extract_ai_response(raw, profile)
    logger.info("%s response: %d chars (raw: %d)", profile.name, len(response), len(raw))
    return response


def send_prompt_and_get_response(
    hwnd: int,
    prompt: str,
    profile: AIProfile = GEMINI_PROFILE,
    timeout: float = MAX_GENERATE_WAIT,
    on_progress: Optional[callable] = None,
    cancel_event=None,
) -> str:
    """Full cycle: send -> wait -> read. Used when NOT using traffic controller.
    For traffic-controlled sessions, use the 3-phase API instead.
    """
    send_prompt_phase(hwnd, prompt, profile)

    wait_for_generation_done(
        hwnd, prompt_length=len(prompt), profile=profile,
        timeout=timeout, on_progress=on_progress,
        cancel_event=cancel_event,
    )

    time.sleep(POST_GENERATE_WAIT)
    return read_response_phase(hwnd, profile)
