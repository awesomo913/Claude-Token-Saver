"""Universal window management for AI browser automation.

Finds and positions ANY window — Chrome, Edge, Firefox, Electron apps,
native desktop apps. Not limited to Chrome.
"""

import ctypes
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import ctypes.wintypes
    WIN32_AVAILABLE = True
except Exception:
    WIN32_AVAILABLE = False


@dataclass
class WindowRect:
    """Screen rectangle."""
    x: int
    y: int
    width: int
    height: int


@dataclass
class ScreenInfo:
    """Screen dimensions."""
    width: int
    height: int


def get_screen_size() -> ScreenInfo:
    """Get primary monitor resolution."""
    if WIN32_AVAILABLE:
        user32 = ctypes.windll.user32
        return ScreenInfo(
            width=user32.GetSystemMetrics(0),
            height=user32.GetSystemMetrics(1),
        )
    return ScreenInfo(width=1920, height=1080)


def get_quarter_rect(
    corner: str = "bottom-right",
    screen: Optional[ScreenInfo] = None,
    taskbar_height: int = 48,
) -> WindowRect:
    """Get a 1/4 screen rectangle for a given corner."""
    if screen is None:
        screen = get_screen_size()

    hw = screen.width // 2
    hh = (screen.height - taskbar_height) // 2

    positions = {
        "top-left": WindowRect(0, 0, hw, hh),
        "top-right": WindowRect(hw, 0, hw, hh),
        "bottom-left": WindowRect(0, hh, hw, hh),
        "bottom-right": WindowRect(hw, hh, hw, hh),
    }

    return positions.get(corner, positions["bottom-right"])


# ── Universal window finding ──────────────────────────────────────

def find_windows_by_title(pattern: str) -> list[int]:
    """Find ALL visible windows whose title contains the pattern (case-insensitive).

    Works with Chrome, Edge, Firefox, Electron apps, native apps — any window.
    No class name filtering, so it catches everything.
    """
    if not WIN32_AVAILABLE or not pattern:
        return []

    pattern_lower = pattern.lower()
    handles = []
    user32 = ctypes.windll.user32

    def enum_callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if pattern_lower in buf.value.lower():
                    handles.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return handles


def find_chrome_windows() -> list[int]:
    """Backward compat: find Chrome windows."""
    return find_windows_by_title("chrome")


# ── Window positioning ────────────────────────────────────────────

def move_window(hwnd: int, rect: WindowRect) -> bool:
    """Move and resize a window by its handle."""
    if not WIN32_AVAILABLE:
        return False
    try:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.1)
        result = user32.MoveWindow(hwnd, rect.x, rect.y, rect.width, rect.height, True)
        return bool(result)
    except Exception as e:
        logger.error("Failed to move window: %s", e)
        return False


def position_existing_window(hwnd: int, corner: str = "bottom-right") -> bool:
    """Reposition an existing window to a quarter of the screen."""
    rect = get_quarter_rect(corner)
    return move_window(hwnd, rect)


def find_and_position_window(title_pattern: str, corner: str) -> Optional[int]:
    """Find a window by title pattern and move it to the given corner.

    Returns the hwnd if found and positioned, None otherwise.
    """
    handles = find_windows_by_title(title_pattern)
    if not handles:
        return None

    hwnd = handles[0]
    rect = get_quarter_rect(corner)
    move_window(hwnd, rect)
    logger.info("Found and positioned '%s' window (hwnd=%d) to %s",
                title_pattern, hwnd, corner)
    return hwnd


# ── Browser launching ─────────────────────────────────────────────

# Known browser paths on Windows
BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
}


def _find_browser_exe(browser: str) -> Optional[str]:
    """Find a browser executable on disk."""
    if browser == "any":
        # Try Chrome first, then Edge, then Firefox
        for b in ["chrome", "edge", "firefox"]:
            exe = _find_browser_exe(b)
            if exe:
                return exe
        return None

    paths = BROWSER_PATHS.get(browser, [])
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def launch_to_url(
    url: str,
    corner: str = "bottom-right",
    browser: str = "chrome",
    title_pattern: str = "",
    enable_cdp: bool = True,
    cdp_port: int = 9222,
) -> Optional[int]:
    """Launch a browser to a URL, position to corner, return hwnd.

    Args:
        url: The URL to open
        corner: Screen corner to position the window
        browser: Which browser ("chrome", "edge", "firefox", "any")
        title_pattern: Pattern to find the window after launch
        enable_cdp: Add --remote-debugging-port for CDP automation
        cdp_port: Port for Chrome DevTools Protocol
    """
    if not url:
        return None

    rect = get_quarter_rect(corner)
    browser_exe = _find_browser_exe(browser)

    if not browser_exe:
        logger.error("Browser '%s' not found on this system", browser)
        return None

    args = [browser_exe]

    # Browser-specific window sizing args
    if "chrome" in browser_exe.lower() or "edge" in browser_exe.lower():
        args.extend([
            f"--window-size={rect.width},{rect.height}",
            f"--window-position={rect.x},{rect.y}",
            "--new-window",
        ])
        # Enable CDP for reliable automation
        if enable_cdp:
            args.append(f"--remote-debugging-port={cdp_port}")
    elif "firefox" in browser_exe.lower():
        args.extend([
            f"-width={rect.width}",
            f"-height={rect.height}",
        ])

    args.append(url)

    try:
        subprocess.Popen(args)
        logger.info("Launched %s to %s at %s corner", browser, url, corner)
    except FileNotFoundError:
        logger.error("Failed to launch %s", browser_exe)
        return None

    # Wait for window to appear
    time.sleep(3)

    # Find the window
    if title_pattern:
        handles = find_windows_by_title(title_pattern)
    else:
        # Try to guess from URL
        domain = url.split("//")[-1].split("/")[0].split(".")[0]
        handles = find_windows_by_title(domain)

    for hwnd in handles:
        move_window(hwnd, rect)
        logger.info("Found and positioned launched window: hwnd=%d", hwnd)
        return hwnd

    # Fallback: if we can't find by title, try the browser name
    if browser != "any":
        browser_name = os.path.basename(browser_exe).split(".")[0]
        handles = find_windows_by_title(browser_name)
        if handles:
            move_window(handles[0], rect)
            return handles[0]

    return None


# ── Window capture (click-to-assign) ──────────────────────────────

def get_foreground_window() -> Optional[int]:
    """Get the currently focused/foreground window handle."""
    if not WIN32_AVAILABLE:
        return None
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd and ctypes.windll.user32.IsWindow(hwnd):
            return hwnd
    except Exception:
        pass
    return None


def get_window_title(hwnd: int) -> str:
    """Get a window's title by handle."""
    if not WIN32_AVAILABLE:
        return ""
    try:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""


def capture_foreground_and_position(corner: str, delay: float = 3.0) -> Optional[tuple[int, str]]:
    """Wait for user to click a window, then capture and position it.

    Returns (hwnd, window_title) or None. The delay gives the user time
    to click the target window.
    """
    time.sleep(delay)
    hwnd = get_foreground_window()
    if not hwnd:
        return None

    title = get_window_title(hwnd)
    rect = get_quarter_rect(corner)
    move_window(hwnd, rect)
    logger.info("Captured window '%s' (hwnd=%d) to %s", title[:60], hwnd, corner)
    return (hwnd, title)


def list_candidate_windows() -> list[tuple[int, str, str]]:
    """List all visible windows that could be AI chat interfaces.

    Returns [(hwnd, class_name, title), ...] for windows that look
    like browsers or chat apps (not system windows).
    """
    if not WIN32_AVAILABLE:
        return []

    results = []
    user32 = ctypes.windll.user32
    # Window classes that are likely AI chat candidates
    good_classes = {"Chrome_WidgetWin_1", "MozillaWindowClass", "CabinetWClass",
                    "ApplicationFrameWindow", "CASCADIA_HOSTING_WINDOW_CLASS",
                    "Electron", "TkTopLevel"}
    skip_titles = {"program manager", "settings", "nvidia", "app center",
                   "file explorer", "task manager"}

    def enum_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 5:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                class_name = cls.value

                title_lower = title.lower()
                if not any(s in title_lower for s in skip_titles):
                    results.append((hwnd, class_name, title))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return results


# Legacy alias
def launch_chrome_to_gemini(
    url: str = "https://gemini.google.com/app",
    corner: str = "bottom-right",
) -> Optional[int]:
    """Legacy: launch Chrome to Gemini."""
    return launch_to_url(url, corner, browser="chrome", title_pattern="gemini")
