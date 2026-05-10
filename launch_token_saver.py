"""Entry point for PyInstaller — bootstraps claude_backend as a package.

Modes:
  ClaudeTokenSaver.exe              → opens GUI window (default)
  ClaudeTokenSaver.exe --tray       → starts system-tray icon only
  ClaudeTokenSaver.exe --overlay    → starts floating overlay button only

Crash safety: any uncaught exception is written to
~/.claude/token_saver_crash.log with timestamp + traceback.

Frozen-windowed safety: PyInstaller's --windowed flag sets sys.stdout
and sys.stderr to None. ANY code that writes to them (logging,
traceback, print) crashes with "'NoneType' object has no attribute
'write'". The neutralizer below redirects them to a real file the
moment the script starts — before any import that might log — so
every downstream module (overlay, hotkey, tray, gui) can call
logging.basicConfig() and traceback.print_exc() safely.
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def _neutralize_none_streams() -> None:
    """Redirect None stdout/stderr (frozen --windowed) to a log file.

    Idempotent: a no-op when streams are already real (dev runs, console
    attached). Falls back to os.devnull if the log file can't be opened
    (read-only homedir, etc.) — never raises.

    Must be called BEFORE importing anything that might log on import.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_path = Path.home() / ".claude" / "token_saver_console.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # line-buffered append so multiple subprocesses can interleave safely
        sink = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        sink = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = sink
    if sys.stderr is None:
        sys.stderr = sink


# Apply BEFORE any other import. Frozen --windowed exes will otherwise
# crash on the first logging.basicConfig() call inside any subcommand.
_neutralize_none_streams()

import traceback  # noqa: E402  — must come after stream neutralizer

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


def _is_overlay_mode() -> bool:
    """Overlay mode if --overlay anywhere in argv."""
    return "--overlay" in sys.argv[1:]


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
    if _is_overlay_mode():
        from claude_backend.overlay import main as overlay_main
        return int(overlay_main() or 0)
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
        # Print to stderr too, in case console is attached (dev runs). Wrap
        # in defensive try blocks because stderr can be a write-failed
        # devnull if the home directory was unwritable at startup.
        try:
            traceback.print_exc()
        except Exception:
            pass
        if log:
            try:
                sys.stderr.write(f"\nCrash log: {log}\n")
            except Exception:
                pass
        sys.exit(1)
