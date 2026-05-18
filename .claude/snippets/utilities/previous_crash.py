# From: claude_backend/diagnostics_logger.py:139
# Inspect tail of the most-recent log file across recent days.

def previous_crash() -> dict | None:
    """Inspect tail of the most-recent log file across recent days.

    Returns a small dict {when, exc_type, snippet, log_path} when the
    most-recent STARTUP boundary in the rolled log files was followed by
    a CRASH (and NOT a clean STATE shutdown). Returns None otherwise.

    Intended for GUI cold-start to surface a toast when the prior session
    ended badly, without forcing the user to grep the log.
    """
    if _LOG_PATH is None:
        return None
    candidates: list[Path] = [_LOG_PATH]
    yest = _LOG_PATH.parent.parent / (
        _dt.date.today() - _dt.timedelta(days=1)
    ).isoformat() / _LOG_PATH.name
    if yest.is_file():
        candidates.append(yest)

    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        last_startup_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if "STARTUP" in lines[i]:
                last_startup_idx = i
                break
        if last_startup_idx < 0:
            continue
        prior_startup = -1
        for i in range(last_startup_idx - 1, -1, -1):
            if "STARTUP" in lines[i]:
                prior_startup = i
                break
        if prior_startup < 0:
            return None
        prior_block = lines[prior_startup:last_startup_idx]
        crashed = any("CRASH" in ln for ln in prior_block)
        clean = any("shutdown" in ln.lower() and "STATE" in ln
                    for ln in prior_block)
        if crashed and not clean:
            crash_line = next((ln for ln in prior_block if "CRASH" in ln),
                              "(no detail)")
            exc_type = ""
            for ln in prior_block:
                if ln.strip().startswith("CRASH ") and " " in ln.strip()[6:]:
                    head = ln.strip()[6:].split("\n", 1)[0]
                    exc_type = head.split()[0] if head else ""
                    break
            when = prior_block[0].split(" ")[0] if prior_block else ""
            return {
                "when": when,
                "exc_type": exc_type or "Exception",
                "snippet": crash_line[:160],
                "log_path": str(path),
            }
    return None
