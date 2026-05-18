"""Frozen-exe-safe diagnostic logger.

Every Claude Token Saver entry point calls `bootstrap(app_name=...)` at
startup. Captures STARTUP, STATE, DECISION, PERF, CRASH lines into a
daily log file under `~/.claude/session-data/YYYY-MM-DD/exe_<AppName>.log`,
per the workspace exe-packaging convention.

Frozen-exe-safe:
- Tolerates `sys.stdout = None` (PyInstaller --windowed)
- Tolerates missing `__file__` (frozen builds)
- Tolerates locked / unwritable log dir (falls back to %TEMP%)

Adapted verbatim from Quasar's tools/diagnostics_logger.py — stdlib only,
no project-specific assumptions.
"""
from __future__ import annotations

import datetime as _dt
import logging
import logging.handlers
import os
import sys
import traceback
from pathlib import Path
from typing import Optional

_INITIALIZED = False
_APP_NAME: Optional[str] = None
_LOG_PATH: Optional[Path] = None


def _log_dir() -> Path:
    """Return today's log dir, with fallback to %TEMP% if home is unwritable."""
    today = _dt.date.today().isoformat()
    primary = Path.home() / ".claude" / "session-data" / today
    try:
        primary.mkdir(parents=True, exist_ok=True)
        probe = primary / ".write_probe"
        probe.touch()
        probe.unlink()
        return primary
    except OSError:
        fallback = Path(os.environ.get("TEMP",
                                       os.environ.get("TMP", "."))) / \
                   ".claude_logs" / today
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _safe_argv() -> list[str]:
    try:
        return list(sys.argv)
    except Exception:  # noqa: BLE001
        return ["<argv unavailable>"]


def _frozen() -> bool:
    return getattr(sys, "frozen", False)


def _python_version() -> str:
    try:
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    except Exception:  # noqa: BLE001
        return "unknown"


def bootstrap(app_name: str, version: str = "0.1.0") -> Path:
    """Initialize the per-app logger. Idempotent: subsequent calls are no-ops."""
    global _INITIALIZED, _APP_NAME, _LOG_PATH
    if _INITIALIZED:
        return _LOG_PATH  # type: ignore[return-value]

    _APP_NAME = app_name
    _LOG_PATH = _log_dir() / f"exe_{app_name}.log"

    handler = logging.handlers.RotatingFileHandler(
        _LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    log = logging.getLogger("startup")
    log.info("STARTUP %s %s v%s python=%s frozen=%s argv=%r",
             _dt.datetime.now().isoformat(timespec="seconds"),
             app_name, version, _python_version(), _frozen(), _safe_argv())

    def _excepthook(exc_type, exc, tb):
        try:
            crash = logging.getLogger("crash")
            crash.error(
                "CRASH %s\n%s",
                exc_type.__name__,
                "".join(traceback.format_exception(exc_type, exc, tb)),
            )
            crash.error("CRASH argv=%r frozen=%s", _safe_argv(), _frozen())
        except Exception:  # noqa: BLE001
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook

    import atexit

    def _shutdown() -> None:
        try:
            logging.getLogger("shutdown").info(
                "STATE %s shutdown",
                _dt.datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:  # noqa: BLE001
            pass

    atexit.register(_shutdown)

    _INITIALIZED = True
    return _LOG_PATH


def state(transition: str) -> None:
    """Log a STATE transition (e.g. 'init->ready', 'ready->shutdown')."""
    logging.getLogger("state").info("STATE %s", transition)


def decision(detail: str) -> None:
    """Log a non-trivial branch (e.g. 'cleanup=skipped reason=no-stale-flag')."""
    logging.getLogger("decision").info("DECISION %s", detail)


def perf(label: str, seconds: float) -> None:
    """Log a timed operation (e.g. perf('tk_root_init', 0.42))."""
    logging.getLogger("perf").info("PERF %s=%.3fs", label, seconds)


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
