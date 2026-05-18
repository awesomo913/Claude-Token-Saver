# From: claude_backend/tracker.py:224
# Suggest snippets related to what's in the current context queue.

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
