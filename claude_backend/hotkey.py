"""Global hotkey daemon for Phase 3.

Registers a system-wide keyboard shortcut (default Ctrl+Shift+I). When
fired, runs the same capture-improve pipeline as the overlay button:

  1. Send Ctrl+A then Ctrl+C to whatever window has focus.
  2. Read clipboard.
  3. POST captured text + last-used project to /improve.

Unlike the overlay, the hotkey has no visible UI of its own. The Token
Saver GUI's pending-file watcher picks up the response and pops the
Builder tab pre-populated.

Implementation note: the `keyboard` library installs a low-level
Windows hook. On some corporate machines this requires elevated rights;
when registration fails, a clean error message is logged and the daemon
exits gracefully — no crash.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from pathlib import Path

try:
    import keyboard
except ImportError:
    keyboard = None  # type: ignore[assignment]

try:
    import pyperclip
except ImportError:
    pyperclip = None  # type: ignore[assignment]

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None  # type: ignore[assignment]

from .prefs import Prefs

logger = logging.getLogger(__name__)

_thread: threading.Thread | None = None
_registered_combo: str | None = None
_lock = threading.Lock()


def _capture_and_improve() -> None:
    """Triggered by hotkey press. Runs in a fresh thread each fire."""
    if pyautogui is None or pyperclip is None:
        logger.warning("Hotkey trigger requires pyautogui + pyperclip")
        return

    try:
        prefs = Prefs.load()

        # Save and restore clipboard so the user's normal clipboard
        # contents aren't permanently overwritten by our select-all+copy.
        saved = ""
        try:
            saved = pyperclip.paste()
        except Exception:
            pass

        # Select-all + copy in the focused window. Hotkey already
        # consumed the Ctrl+Shift+I keystroke; we send fresh keystrokes.
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.1)

        captured = ""
        try:
            captured = pyperclip.paste()
        except Exception as e:
            logger.warning("Clipboard read failed: %s", e)

        captured = (captured or "").strip()
        if not captured:
            logger.info("Hotkey: empty clipboard, aborting")
            return

        # Use last_project_path. Hotkey path doesn't show a picker — too
        # disruptive when fired from a terminal. User picks via GUI/overlay
        # if they want a different project.
        project_path = prefs.last_project_path or ""

        body = json.dumps({
            "prompt": captured, "project_path": project_path,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{prefs.http_port}/improve",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            _ = r.read()

        # Restore clipboard (best-effort).
        if saved:
            try:
                pyperclip.copy(saved)
            except Exception:
                pass
    except Exception as e:
        logger.warning("Hotkey pipeline failed: %s", e)


def _on_hotkey() -> None:
    # Run pipeline in a daemon thread — keyboard library requires the
    # callback to return quickly so its hook stays responsive.
    threading.Thread(target=_capture_and_improve, daemon=True).start()


def start(combo: str | None = None) -> bool:
    """Register the global hotkey. Returns True on success.

    Idempotent: re-registers if combo changed; no-op if same combo
    already active.
    """
    global _thread, _registered_combo

    if keyboard is None:
        logger.warning("keyboard library not available; hotkey disabled")
        return False

    with _lock:
        if combo is None:
            combo = Prefs.load().hotkey_combo

        if _registered_combo == combo and _thread is not None and _thread.is_alive():
            return True  # already running with same combo

        # Tear down existing registration if any
        try:
            if _registered_combo:
                keyboard.remove_hotkey(_registered_combo)
        except Exception as e:
            logger.debug("Failed to remove old hotkey: %s", e)

        try:
            keyboard.add_hotkey(combo, _on_hotkey, suppress=False)
        except Exception as e:
            logger.warning(
                "Hotkey registration failed for '%s': %s. "
                "On corporate Windows this can require admin rights.",
                combo, e,
            )
            return False

        _registered_combo = combo

        # Spawn a daemon thread that just keeps the hook alive.
        # `keyboard.add_hotkey` already sets up the OS-level hook; we
        # just need a thread to track 'aliveness' for status reporting.
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(
                target=_keep_alive, name="token_saver_hotkey", daemon=True,
            )
            _thread.start()

        logger.info("Hotkey '%s' registered", combo)
        return True


def _keep_alive() -> None:
    # Idle loop — `keyboard` library's hooks run on a separate thread,
    # but we keep this thread alive so is_running() reports correctly.
    while _registered_combo:
        try:
            time.sleep(5)
        except Exception:
            break


def stop() -> None:
    """Unregister the hotkey. Idempotent."""
    global _registered_combo, _thread
    with _lock:
        if keyboard is not None and _registered_combo:
            try:
                keyboard.remove_hotkey(_registered_combo)
            except Exception as e:
                logger.debug("Failed to remove hotkey: %s", e)
        _registered_combo = None
        # _thread will exit on next loop iteration


def is_running() -> bool:
    """True if hotkey is currently registered."""
    return _registered_combo is not None and _thread is not None and _thread.is_alive()


def current_combo() -> str | None:
    return _registered_combo
