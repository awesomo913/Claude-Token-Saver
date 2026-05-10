"""System tray icon for Claude Token Saver — passive reminder + quick actions.

Runs in the background. Persistent icon in the system tray. Right-click menu
gives one-click access to GUI, manual prep, and auto-inject status. Single
click on icon opens the GUI.

Launch:  python -m claude_backend tray
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

try:
    import pystray
    from pystray import Menu, MenuItem
except ImportError as e:
    raise SystemExit(
        "pystray is required for tray mode. Install: uv pip install pystray Pillow"
    ) from e

from .auto_inject import check_status

logger = logging.getLogger(__name__)

ICON_SIZE = 64
SNOOZE_FILE = Path.home() / ".claude" / "token_saver_snooze.txt"


def _make_icon_image(installed: bool = True) -> Image.Image:
    """Render a 64x64 tray icon. Green dot = installed, gray = not."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background coin: dark navy circle
    draw.ellipse((4, 4, ICON_SIZE - 4, ICON_SIZE - 4), fill=(30, 60, 110, 255))

    # "T" letter centered
    try:
        font = ImageFont.truetype("seguibl.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    text = "T"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        ((ICON_SIZE - tw) // 2, (ICON_SIZE - th) // 2 - 4),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )

    # Status dot bottom-right: green if installed, gray if not
    dot_color = (16, 124, 16, 255) if installed else (120, 120, 120, 255)
    draw.ellipse((44, 44, 60, 60), fill=dot_color, outline=(255, 255, 255, 255), width=2)

    return img


def _is_snoozed() -> bool:
    """Snooze flag honored only if timestamp is in future."""
    if not SNOOZE_FILE.is_file():
        return False
    try:
        until = float(SNOOZE_FILE.read_text().strip())
        return time.time() < until
    except (ValueError, OSError):
        return False


def _set_snooze(hours: float) -> None:
    SNOOZE_FILE.parent.mkdir(parents=True, exist_ok=True)
    until = time.time() + (hours * 3600)
    SNOOZE_FILE.write_text(str(until), encoding="utf-8")


def _clear_snooze() -> None:
    if SNOOZE_FILE.is_file():
        try:
            SNOOZE_FILE.unlink()
        except OSError:
            pass


def _python_exe() -> str:
    """Find pythonw.exe (no console) on Windows; fallback to sys.executable."""
    exe = Path(sys.executable)
    if exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _spawn_overlay_subprocess() -> None:
    """Spawn the overlay as a detached subprocess.

    Uses the deployed exe when available (frozen mode); falls back to
    `python -m claude_backend.overlay` for dev runs. Single-instance
    lock inside the overlay module guarantees no duplicate windows.
    """
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    exe_path = Path.home() / "Desktop" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"
    if exe_path.is_file():
        # Pass --overlay flag so the launcher routes to overlay mode.
        args = [str(exe_path), "--overlay"]
    else:
        args = [_python_exe(), "-m", "claude_backend.overlay"]

    subprocess.Popen(args, creationflags=creationflags, close_fds=True)


def _launch_gui(icon: Optional["pystray.Icon"] = None) -> None:
    """Open Token Saver GUI in detached subprocess."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    try:
        subprocess.Popen(
            [_python_exe(), "-m", "claude_backend.gui"],
            creationflags=creationflags,
            close_fds=True,
        )
    except OSError as e:
        logger.error("Failed to launch GUI: %s", e)


def _run_prep(icon: "pystray.Icon") -> None:
    """Run prep on current working directory. Notify on completion."""
    cwd = Path.cwd()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "claude_backend", "prep", str(cwd), "--quiet"],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode == 0:
            icon.notify("Prep complete", f"Refreshed context for {cwd.name}")
        else:
            icon.notify("Prep failed", "Check logs for details")
    except subprocess.TimeoutExpired:
        icon.notify("Prep timed out", "Aborted after 2 minutes")
    except OSError as e:
        icon.notify("Prep error", str(e))


def _snooze_action(icon: "pystray.Icon", hours: float) -> None:
    _set_snooze(hours)
    icon.notify("Snoozed", f"Reminders paused for {hours:g}h")


def _unsnooze_action(icon: "pystray.Icon") -> None:
    _clear_snooze()
    icon.notify("Resumed", "Reminders active")


def _status_label() -> str:
    s = check_status()
    if s["installed"]:
        return "Auto-Inject: INSTALLED"
    if not s["settings_valid"]:
        return "Auto-Inject: settings.json INVALID"
    return "Auto-Inject: NOT installed"


def _quit_action(icon: "pystray.Icon") -> None:
    icon.stop()


def build_menu() -> Menu:
    """Tray right-click menu. Default item (single-click) opens GUI."""
    return Menu(
        MenuItem("Open Token Saver GUI", _launch_gui, default=True),
        Menu.SEPARATOR,
        MenuItem("Run prep on current folder", _run_prep),
        MenuItem(lambda _: _status_label(), None, enabled=False),
        Menu.SEPARATOR,
        MenuItem(
            "Snooze",
            Menu(
                MenuItem("1 hour", lambda icon, _: _snooze_action(icon, 1)),
                MenuItem("4 hours", lambda icon, _: _snooze_action(icon, 4)),
                MenuItem("Until tomorrow", lambda icon, _: _snooze_action(icon, 12)),
                MenuItem("Resume reminders", _unsnooze_action),
            ),
        ),
        Menu.SEPARATOR,
        MenuItem("Quit", _quit_action),
    )


_TRAY_INSTANCE_NAME = "ClaudeTokenSaverTray"


def run() -> int:
    """Start tray icon. Blocks until user picks Quit.

    Single-instance enforced via Windows named mutex (with pidfile
    fallback). If another tray is already running, this call exits 0
    immediately — no duplicate icon.

    Also boots the localhost HTTP server (Phase 0 backend) in a daemon
    thread so the browser extension / overlay / hotkey can talk to us.
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    # Acquire single-instance lock. Held in `_lock` for process lifetime.
    from .single_instance import acquire_or_exit
    _lock = acquire_or_exit(_TRAY_INSTANCE_NAME)  # noqa: F841 (intentional)

    # Boot HTTP server. Best-effort: failure logs but doesn't block tray.
    try:
        from . import http_server
        from .prefs import Prefs
        prefs = Prefs.load()
        if http_server.start_server(prefs.http_port):
            logger.info("HTTP server started on 127.0.0.1:%d", prefs.http_port)
        else:
            logger.warning(
                "HTTP server failed to start on port %d (already in use?). "
                "Browser extension and overlay button will not work.",
                prefs.http_port,
            )
    except Exception as e:
        logger.warning("HTTP server boot failed: %s", e)
        prefs = None  # type: ignore[assignment]

    # Spawn overlay as detached subprocess if pref is on. Overlay has its
    # own Tk root + single-instance lock, so it survives independently.
    if prefs is not None and prefs.show_overlay:
        try:
            _spawn_overlay_subprocess()
        except Exception as e:
            logger.warning("Overlay spawn failed: %s", e)

    # Auto-start Ollama daemon if installed and pref is on, so local
    # AI models are reachable as soon as Token Saver is up. Runs in a
    # background thread because start_daemon polls up to 8s for the
    # server to become reachable. Failure is non-fatal — Settings shows
    # "Ollama not running" and download buttons surface a friendly
    # toast (handled in gui.py).
    if prefs is not None and getattr(prefs, "auto_start_ollama", True):
        try:
            from .ollama_manager import OllamaManager

            def _boot_ollama() -> None:
                try:
                    OllamaManager().start_daemon(wait_seconds=8.0)
                except Exception as e:
                    logger.warning("Ollama auto-start failed: %s", e)

            threading.Thread(
                target=_boot_ollama, daemon=True,
                name="ts_ollama_autostart",
            ).start()
        except Exception as e:
            logger.warning("Ollama auto-start dispatch failed: %s", e)

    # Register global hotkey if pref is on. keyboard library installs an
    # OS-level hook in the current process — runs in tray process.
    if prefs is not None and prefs.enable_hotkey:
        try:
            from . import hotkey
            if hotkey.start(prefs.hotkey_combo):
                logger.info("Global hotkey '%s' active", prefs.hotkey_combo)
            else:
                logger.warning(
                    "Global hotkey registration failed; check admin rights",
                )
        except Exception as e:
            logger.warning("Hotkey boot failed: %s", e)

    status = check_status()
    icon_img = _make_icon_image(installed=status["installed"])

    icon = pystray.Icon(
        "claude_token_saver",
        icon=icon_img,
        title="Claude Token Saver",
        menu=build_menu(),
    )

    # Refresh icon dot every 30s — picks up auto-inject install/uninstall.
    # Wrap each iteration so a single exception cannot kill the loop and
    # freeze the icon's status indicator forever.
    def refresh_loop() -> None:
        while True:
            try:
                time.sleep(30)
                s = check_status()
                icon.icon = _make_icon_image(installed=s["installed"])
            except Exception as e:
                logger.warning("Icon refresh iteration failed: %s", e)
                # Brief backoff before next attempt to avoid log spam if
                # the underlying issue is persistent (e.g. corrupt JSON).
                try:
                    time.sleep(10)
                except Exception:
                    pass

    threading.Thread(target=refresh_loop, daemon=True).start()

    icon.run()
    return 0


if __name__ == "__main__":
    sys.exit(run())
