# From: claude_backend/single_instance.py:87
# Idempotent — release mutexes on clean shutdown so an

def _register_atexit_release() -> None:
    """Idempotent — release mutexes on clean shutdown so an
    immediate-restart scenario sees the slot free."""
    global _ATEXIT_REGISTERED
    if _ATEXIT_REGISTERED:
        return
    _ATEXIT_REGISTERED = True

    def _release_all() -> None:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            for h in _HELD_HANDLES:
                try:
                    kernel32.ReleaseMutex(h)
                except Exception:
                    pass
                try:
                    kernel32.CloseHandle(h)
                except Exception:
                    pass
            _HELD_HANDLES.clear()
        except Exception:
            pass

    atexit.register(_release_all)
