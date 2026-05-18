# From: claude_backend/tracker.py:37

    def _load(self) -> None:
        if not self.path.is_file():
            return
        with _LEDGER_LOCK:
            try:
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        self._events.append(json.loads(line))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load token tracker: %s", e)
