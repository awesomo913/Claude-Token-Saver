# From: claude_backend/diagnostics_logger.py:83
# Initialize the per-app logger. Idempotent: subsequent calls are no-ops.

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
