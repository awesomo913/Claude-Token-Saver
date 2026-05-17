# From: claude_backend/single_instance.py:46
# Try to create a named mutex. Returns (acquired, handle).

def _acquire_windows_mutex(name: str) -> tuple[bool, Any]:
    """Try to create a named mutex. Returns (acquired, handle).

    handle stays in scope for process lifetime to keep mutex alive.
    Caller should keep a reference even though handle is opaque.
    """
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return False, None

    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE

        # Prefix with "Local\" so the mutex is per-user-session, not global.
        # Avoids cross-user-session collisions on shared Windows machines.
        full_name = f"Local\\{name}"
        handle = kernel32.CreateMutexW(None, False, full_name)
        last_err = kernel32.GetLastError()
        if not handle:
            logger.debug("CreateMutexW returned NULL (err=%d)", last_err)
            return False, None
        if last_err == _ERROR_ALREADY_EXISTS:
            # Another process owns it. Close our handle to avoid leak.
            kernel32.CloseHandle(handle)
            return False, None
        # v0.7.0 — also retain a module-global ref so the mutex
        # outlives careless callers + GC pressure during init.
        _HELD_HANDLES.append(handle)
        _register_atexit_release()
        return True, handle
    except Exception as e:
        logger.debug("Windows mutex path failed: %s", e)
        return False, None
