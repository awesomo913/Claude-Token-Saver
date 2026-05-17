# From: claude_backend/session_launcher.py:75
# Entry point. Always exits 0 to avoid blocking session start.

def main() -> int:
    """Entry point. Always exits 0 to avoid blocking session start.

    Decision tree:
      1. auto_launch_gui_on_session OFF       -> exit 0 (no-op)
      2. minimized=True (tray reminder mode)  -> if tray running, no-op;
                                                 else spawn `exe --tray`
      3. minimized=False (full window mode)   -> if GUI window already
                                                 running, no-op; else
                                                 spawn `exe` (full GUI)

    The tray and the GUI window have separate single-instance locks
    so they can coexist (tray is always-on indicator; GUI window is
    per-session reminder). Closing the GUI window releases its lock,
    so the next Claude Code session re-spawns the window.
    """
    prefs = Prefs.load()

    if not prefs.auto_launch_gui_on_session:
        return 0

    # Choose target based on mode.
    want_tray = prefs.auto_launch_minimized
    target_lock = _TRAY_INSTANCE_NAME if want_tray else _GUI_INSTANCE_NAME

    # Skip if the requested target is already running.
    if is_locked(target_lock):
        return 0

    exe = _find_exe()
    if exe is None:
        # Frozen exe missing — fall back to running from source.
        py = sys.executable
        if sys.platform == "win32":
            cand = Path(py).with_name("pythonw.exe")
            if cand.is_file():
                py = str(cand)
        if want_tray:
            python_args = [py, "-m", "claude_backend", "tray"]
        else:
            python_args = [py, "-m", "claude_backend.gui"]
        _spawn_detached(python_args)
        return 0

    args: list[str] = [str(exe)]
    if want_tray:
        args.append("--tray")
    _spawn_detached(args)
    return 0
