"""Token savings tracker and session context memory."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
#  Token Savings Tracker  (global, persistent across projects)
# ═══════════════════════════════════════════════════════════════════════════

class TokenTracker:
    """Persistent token savings counter stored in ~/.claude/token_savings.jsonl."""

    def __init__(self) -> None:
        self.path = Path.home() / ".claude" / "token_savings.jsonl"
        self._events: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self._events.append(json.loads(line))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load token tracker: %s", e)

    def _append(self, event: dict) -> None:
        self._events.append(event)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to write token event: %s", e)

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


# ═══════════════════════════════════════════════════════════════════════════
#  Session Context Memory  (per-project, tracks what Claude has seen)
# ═══════════════════════════════════════════════════════════════════════════

class SessionMemory:
    """Tracks what's been sent to Claude in a project's context.

    Stored at {project}/.claude/session_context.json.
    Enables: recently-used items, related suggestions, connection tracking.
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        self._project = project_path
        self._data: dict = {
            "context_history": [],    # items added to context
            "clipboard_copies": [],   # full context copies
            "connections": {},        # module -> [snippet names] for suggestions
        }
        if project_path:
            self._path = project_path / ".claude" / "session_context.json"
            self._load()
        else:
            self._path = None

    def set_project(self, project_path: Path) -> None:
        self._project = project_path
        self._path = project_path / ".claude" / "session_context.json"
        self._load()

    def _load(self) -> None:
        if not self._path or not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = raw
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load session memory: %s", e)

    def _save(self) -> None:
        if not self._path:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning("Failed to save session memory: %s", e)

    # ── Recording events ───────────────────────────────────────────────

    def record_context_add(
        self, name: str, source: str, file_path: str = "", tokens: int = 0,
    ) -> None:
        """Record that an item was added to the context builder."""
        entry = {
            "name": name,
            "source": source,
            "file_path": file_path,
            "tokens": tokens,
            "ts": _now(),
        }
        history = self._data.setdefault("context_history", [])
        # Deduplicate: remove older entry with same name+source
        history[:] = [h for h in history if not (h["name"] == name and h["source"] == source)]
        history.append(entry)
        # Keep last 100
        if len(history) > 100:
            history[:] = history[-100:]

        # Update connection graph: track which module this snippet is from
        if file_path:
            module = file_path.split("/")[0] if "/" in file_path else file_path
            conns = self._data.setdefault("connections", {})
            names_in_module = conns.setdefault(module, [])
            if name not in names_in_module:
                names_in_module.append(name)

        self._save()

    def record_clipboard_copy(
        self, template: str, item_count: int, tokens: int,
    ) -> None:
        """Record a context-to-clipboard copy."""
        copies = self._data.setdefault("clipboard_copies", [])
        copies.append({
            "template": template,
            "items": item_count,
            "tokens": tokens,
            "ts": _now(),
        })
        if len(copies) > 50:
            copies[:] = copies[-50:]
        self._save()

    # ── Querying ───────────────────────────────────────────────────────

    def get_recently_used(self, limit: int = 15) -> list[dict]:
        """Get most recently added context items (newest first)."""
        history = self._data.get("context_history", [])
        return list(reversed(history[-limit:]))

    def get_total_copies(self) -> int:
        return len(self._data.get("clipboard_copies", []))

    def get_total_context_items(self) -> int:
        return len(self._data.get("context_history", []))

    def suggest_related(self, current_queue: list[dict]) -> list[dict]:
        """Suggest snippets related to what's in the current context queue.

        Logic: if queue contains snippet from module X, suggest other
        snippets from module X that aren't already in the queue.
        """
        if not current_queue:
            return []

        # Find modules represented in the queue
        queue_names = {item.get("name", "") for item in current_queue}
        queue_modules: set[str] = set()
        for item in current_queue:
            src = item.get("source", "")
            if "/" in src:
                queue_modules.add(src.split("/")[0])
            # Also check file_path from history
            fp = item.get("file_path", "")
            if "/" in fp:
                queue_modules.add(fp.split("/")[0])

        # Also match modules from connection graph
        conns = self._data.get("connections", {})
        for item in current_queue:
            name = item.get("name", "")
            for module, names in conns.items():
                if name in names:
                    queue_modules.add(module)

        # Find history items from those modules not in queue
        suggestions: list[dict] = []
        seen: set[str] = set()
        history = self._data.get("context_history", [])
        for entry in reversed(history):
            name = entry.get("name", "")
            if name in queue_names or name in seen:
                continue
            fp = entry.get("file_path", "")
            module = fp.split("/")[0] if "/" in fp else ""
            if module in queue_modules:
                suggestions.append(entry)
                seen.add(name)
            if len(suggestions) >= 8:
                break

        return suggestions

    def get_activity_summary(self) -> dict:
        """Summary for dashboard display."""
        history = self._data.get("context_history", [])
        copies = self._data.get("clipboard_copies", [])
        return {
            "total_items_added": len(history),
            "total_copies": len(copies),
            "unique_snippets": len({h["name"] for h in history}),
            "total_tokens_copied": sum(c.get("tokens", 0) for c in copies),
            "last_activity": history[-1]["ts"] if history else None,
        }
