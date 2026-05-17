# From: claude_backend/single_instance.py:191
# Try to acquire a single-instance lock. Exit cleanly if already held.

def acquire_or_exit(name: str, exit_code: int = 0) -> Any:
    """Try to acquire a single-instance lock. Exit cleanly if already held.

    Returns an opaque handle (Windows mutex + pidfile, or pidfile alone).
    Caller must keep this in scope for the process lifetime — letting it
    be garbage-collected releases the mutex early.

    On Windows: tries named mutex first (primary enforcement). On success
    ALSO writes a PID lockfile so external processes can detect via
    `is_locked()` without needing to attempt mutex acquisition. If mutex
    creation fails entirely (rare), falls back to pidfile only.

    On other platforms: pidfile only.

    Exits the process via sys.exit if another instance is detected.
    """
    if sys.platform == "win32":
        ok, handle = _acquire_windows_mutex(name)
        if ok:
            # Mutex acquired; also write pidfile (advisory, for is_locked()).
            _acquire_pidfile(name)
            return handle
        if handle is None:
            # Mutex creation failed entirely — fall back to pidfile.
            ok2, pidfile = _acquire_pidfile(name)
            if ok2:
                return pidfile
        # v0.7.0 — request the running instance to surface its window,
        # then exit. Replaces silent exit so double-launching doesn't
        # feel broken to the user.
        logger.info(
            "Another instance of %s is already running; "
            "requesting it to surface, then exiting.", name,
        )
        _request_bring_to_front(name)
        sys.exit(exit_code)

    # Non-Windows path.
    ok, pidfile = _acquire_pidfile(name)
    if ok:
        return pidfile
    logger.info(
        "Another instance of %s is already running; "
        "requesting it to surface, then exiting.", name,
    )
    _request_bring_to_front(name)
    sys.exit(exit_code)
