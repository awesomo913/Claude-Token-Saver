# From: claude_backend/tracker.py:103
# Break down tokens saved by operation type.

    def get_operation_breakdown(self, project: str = "") -> dict[str, int]:
        """Break down tokens saved by operation type."""
        breakdown: dict[str, int] = {}
        for e in self._events:
            if project and e.get("project") != project:
                continue
            op = e.get("op", "unknown")
            breakdown[op] = breakdown.get(op, 0) + e.get("tokens", 0)
        return breakdown
