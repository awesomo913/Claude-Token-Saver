# From: claude_backend/tracker.py:29
# Persistent token savings counter stored in ~/.claude/token_savings.jsonl.

class TokenTracker:
    """Persistent token savings counter stored in ~/.claude/token_savings.jsonl."""

    def __init__(self) -> None:
        self.path = Path.home() / ".claude" / "token_savings.jsonl"
        self._events: list[dict] = []
        self._load()

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

    def _append(self, event: dict) -> None:
        self._events.append(event)
        with _LEDGER_LOCK:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
            except OSError as e:
                logger.error("Failed to write token event: %s", e)

    def record(
        self,
        operation: str,
        tokens: int,
        project: str = "",
        detail: str = "",
        tokens_avoided: int = 0,
    ) -> None:
        """Record a token-saving event.

        Args:
            tokens: tokens actually provided/referenced (the cost)
            tokens_avoided: tokens Claude would have read without the tool (the savings)
        Operations: "clipboard_copy", "bootstrap", "prep", "context_build"
        """
        self._append({
            "ts": _now(),
            "op": operation,
            "tokens": tokens,
            "tokens_avoided": tokens_avoided,
            "project": project,
            "detail": detail,
        })

    def get_all_time_total(self) -> int:
        """Total tokens AVOIDED (real savings, not just referenced)."""
        return sum(e.get("tokens_avoided", e.get("tokens", 0)) for e in self._events)

    def get_project_total(self, project: str) -> int:
        return sum(
            e.get("tokens_avoided", e.get("tokens", 0)) for e in self._events
            if e.get("project") == project
        )

    def get_session_total(self, since_ts: str) -> int:
        """Tokens avoided since a given ISO timestamp (current app session)."""
        return sum(
            e.get("tokens_avoided", e.get("tokens", 0)) for e in self._events
            if e.get("ts", "") >= since_ts
        )

    def get_recent_events(self, limit: int = 20) -> list[dict]:
        return self._events[-limit:]

    def get_operation_breakdown(self, project: str = "") -> dict[str, int]:
        """Break down tokens saved by operation type."""
        breakdown: dict[str, int] = {}
        for e in self._events:
            if project and e.get("project") != project:
                continue
            op = e.get("op", "unknown")
            breakdown[op] = breakdown.get(op, 0) + e.get("tokens", 0)
        return breakdown
