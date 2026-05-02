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


def run() -> int:
    """Start tray icon. Blocks until user picks Quit."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    status = check_status()
    icon_img = _make_icon_image(installed=status["installed"])

    icon = pystray.Icon(
        "claude_token_saver",
        icon=icon_img,
        title="Claude Token Saver",
        menu=build_menu(),
    )

    # Refresh icon dot every 30s — picks up auto-inject install/uninstall
    def refresh_loop() -> None:
        while True:
            time.sleep(30)
            try:
                s = check_status()
                icon.icon = _make_icon_image(installed=s["installed"])
            except Exception as e:
                logger.debug("Icon refresh failed: %s", e)

    threading.Thread(target=refresh_loop, daemon=True).start()

    icon.run()
    return 0


if __name__ == "__main__":
    sys.exit(run())
