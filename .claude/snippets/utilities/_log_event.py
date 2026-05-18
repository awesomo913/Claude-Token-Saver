# From: claude_backend/storage.py:66
# Append an event to the log file.

    def _log_event(self, event: str, path: str, **extra: object) -> None:
        """Append an event to the log file."""
        entry = {"event": event, "path": path, "ts": _now_iso(), **extra}
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to write log: %s", e)
