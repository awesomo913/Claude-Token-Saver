# From: claude_backend/tracker.py:167
# Record that an item was added to the context builder.

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
