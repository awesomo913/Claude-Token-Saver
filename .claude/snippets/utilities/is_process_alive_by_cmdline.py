# From: claude_backend/single_instance.py:263
# Scan running processes for one whose argv contains `needle` as

def is_process_alive_by_cmdline(needle: str) -> bool:
    """Scan running processes for one whose argv contains `needle` as
    an exact argument.

    Authoritative fallback when pidfile lookup races or returns wrong
    answer (e.g. pidfile written under a different `Path.home()` than the
    caller resolves). Slower than `is_locked` (iterates all processes)
    so use only when stronger guarantee is needed.

    Match is exact-element to avoid matching parent shells whose `-c`
    command string happens to contain the needle as a substring (which
    would also surface the calling python interpreter on chained shells).
    Excludes the calling process explicitly as a belt-and-braces guard.
    """
    try:
        import psutil
    except ImportError:
        return False
    self_pid = os.getpid()
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            if p.info.get("pid") == self_pid:
                continue
            cmd = p.info.get("cmdline") or []
            if needle in cmd:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            continue
    return False
