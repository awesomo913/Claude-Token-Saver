# From: claude_backend/overlay.py:679
# Run overlay as its own process with a hidden parent Tk root.

def main() -> int:
    """Run overlay as its own process with a hidden parent Tk root.

    Tray spawns this as a detached subprocess when prefs.show_overlay is
    True, so the overlay is independent of the GUI window's lifetime.
    Single-instance enforced via shared lock (re-launching is a no-op).
    """
    # Frozen-exe-safe structured logger: STARTUP/STATE/DECISION/PERF/CRASH
    # land in ~/.claude/session-data/<date>/exe_Overlay.log per the
    # workspace exe-packaging convention. Replaces the prior ad-hoc
    # _install_overlay_file_logger() — that gave us a file handler but no
    # excepthook, so frozen-exe crashes vanished without stderr.
    from . import __version__
    from .diagnostics_logger import bootstrap, decision, perf, state
    bootstrap(app_name="Overlay", version=__version__)
    state("init")

    _t0 = time.perf_counter()

    # Best-effort cleanup of any stale raise-flag left behind by a
    # previously-crashed overlay instance — otherwise we'd "raise" on
    # boot for a launch attempt that happened long before we started.
    from .single_instance import _flag_path
    _stale_flag = _flag_path(_OVERLAY_INSTANCE_NAME)
    try:
        had_stale = _stale_flag.exists()
        _stale_flag.unlink(missing_ok=True)
        decision(f"stale_flag_cleanup=found={had_stale}")
    except OSError as e:
        logger.debug("stale overlay raise-flag cleanup failed: %s", e)
        decision(f"stale_flag_cleanup=error err={e!r}")

    from .single_instance import acquire_or_exit
    _lock = acquire_or_exit(_OVERLAY_INSTANCE_NAME)  # noqa: F841
    decision("single_instance=acquired")

    # Hidden root window — only exists to host the Toplevel overlay.
    # Defense-in-depth so the root stays invisible even if some Tk
    # action (focus_force on a child, etc.) un-withdraws it:
    #   - tiny 1x1 geometry positioned off the visible area
    #   - alpha 0 so it's transparent if it does surface
    #   - tool-window flag suppresses the taskbar entry
    #   - finally withdraw() to hide it normally
    root = ctk.CTk()
    try:
        root.geometry("1x1+-32000+-32000")
        root.attributes("-alpha", 0.0)
        root.attributes("-toolwindow", True)
    except Exception:
        pass
    root.withdraw()

    button = OverlayButton(root)

    # Raise-flag poller — consumes ~/.claude/ClaudeTokenSaverOverlay_raise.flag
    # written by `acquire_or_exit` when a duplicate `--overlay` launch is
    # rejected. On flag, lift the floating button to the top and briefly
    # toggle topmost so the user sees it move to foreground.
    from .single_instance import poll_bring_to_front_flag

    def _on_raise() -> None:
        try:
            button.lift()
            button.attributes("-topmost", True)
            # 200ms is enough for Windows to honor the topmost re-assert,
            # short enough that the user perceives it as a single flash.
            button.after(200, lambda: button.attributes("-topmost", False))
        except Exception as e:
            logger.debug("overlay raise failed: %s", e)

    def _tick_raise() -> None:
        try:
            poll_bring_to_front_flag(_OVERLAY_INSTANCE_NAME, _on_raise)
        except Exception as e:
            logger.debug("overlay raise-flag poll failed: %s", e)
        try:
            root.after(1500, _tick_raise)
        except Exception as e:
            # TclError during teardown — loop ends naturally.
            logger.debug("overlay raise-flag reschedule failed: %s", e)

    root.after(1500, _tick_raise)

    perf("tk_init", time.perf_counter() - _t0)
    state("init->ready")
    root.mainloop()
    state("ready->shutdown")
    return 0
