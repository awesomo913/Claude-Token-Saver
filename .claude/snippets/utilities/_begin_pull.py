# From: claude_backend/gui.py:2665
# Kick off the actual model pull. Caller must have already

    def _begin_pull(self, name: str) -> None:
        """Kick off the actual model pull. Caller must have already
        verified `self._ollama.is_running()`."""
        self._pull_status.configure(
            text=f"Downloading {name}...", text_color=C["fg"],
        )
        self._pull_progress.set(0)
        self._toast(f"Downloading {name}...", "info")
        self._log(f"Pulling model: {name}")

        def on_progress(pct, status):
            self.after(0, lambda: self._pull_progress.set(pct / 100))
            self.after(0, lambda: self._pull_status.configure(text=f"{status}  {pct:.0f}%"))

        def on_done():
            self.after(0, lambda: self._pull_progress.set(1.0))
            self.after(0, lambda: self._pull_status.configure(text=f"{name} downloaded!"))
            self.after(0, lambda: self._toast(f"Model {name} ready!", "success"))
            self.after(0, lambda: self._log(f"Model downloaded: {name}"))
            self.after(500, self._refresh_models)
            # Auto-select if it's first model
            if not self._ollama.get_current():
                self.after(600, lambda: self._select_model(name))

        def on_error(err):
            # Friendly mapping for the common case where Ollama died
            # mid-pull (or wasn't fully up at the start). Mirrors the
            # pre-check guard so the message stays consistent if the
            # daemon flaps after we passed the guard.
            es = str(err)
            if "10061" in es or "ConnectionRefused" in es or "actively refused" in es:
                friendly = "Ollama daemon stopped — restart Ollama, then retry."
            else:
                friendly = f"Download failed: {err}"
            self.after(0, lambda: self._pull_status.configure(text=friendly))
            self.after(0, lambda: self._toast(friendly, "error"))

        self._ollama.pull_model(name, on_progress=on_progress, on_done=on_done, on_error=on_error)
