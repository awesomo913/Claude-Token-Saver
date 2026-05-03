"""Entry point for PyInstaller — bootstraps claude_backend as a package.

Modes:
  ClaudeTokenSaver.exe          → opens GUI window (default)
  ClaudeTokenSaver.exe --tray   → starts system-tray icon only

Crash safety: any uncaught exception is written to
~/.claude/token_saver_crash.log with timestamp + traceback. Without
this, --windowed PyInstaller builds swallow tracebacks and the user
sees the exe close silently with no indication of what went wrong.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

# When frozen by PyInstaller, _MEIPASS points to the temp extraction dir.
# claude_backend is bundled as data there, so add it to sys.path.
if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


def _is_tray_mode() -> bool:
    """Tray mode if --tray (or -t) anywhere in argv. Other args ignored."""
    return any(a in ("--tray", "-t") for a in sys.argv[1:])


def _log_crash(exc: BaseException) -> Path | None:
    """Write traceback to ~/.claude/token_saver_crash.log. Best-effort.

    Returns the log path if written, else None.
    """
    try:
        log_path = Path.home() / ".claude" / "token_saver_crash.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        mode = "tray" if _is_tray_mode() else "gui"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n=== {ts} (mode={mode}) ===\n")
            f.write(f"argv: {sys.argv}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        return log_path
    except Exception:
        # Never let crash logging itself crash the exit path.
        return None


def _main() -> int:
    if _is_tray_mode():
        from claude_backend.tray import run as tray_run
        return int(tray_run() or 0)
    from claude_backend.gui import main as gui_main
    gui_main()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_main())
    except SystemExit:
        raise
    except BaseException as e:  # noqa: BLE001 — top-level crash handler
        log = _log_crash(e)
        # Print to stderr too, in case console is attached (dev runs).
        try:
            traceback.print_exc()
        except Exception:
            pass
        if log:
            sys.stderr.write(f"\nCrash log: {log}\n")
        sys.exit(1)
