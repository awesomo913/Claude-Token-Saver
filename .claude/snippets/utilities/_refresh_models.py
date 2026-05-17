# From: claude_backend/gui.py:2533
# Refresh the installed model list and combo.

    def _refresh_models(self) -> None:
        """Refresh the installed model list and combo."""
        def do():
            running = self._ollama.is_running()
            models = self._ollama.list_models() if running else []
            return running, models
        def done(result):
            running, models = result
            if running:
                self._ollama_status.configure(text="Ollama: RUNNING", text_color=C["ok"])
            else:
                self._ollama_status.configure(text="Ollama: NOT RUNNING", text_color=C["err"])
            # Update combo
            names = [m["name"] for m in models]
            if names:
                self._model_combo.configure(values=names)
                cur = self._ollama.get_current()
                if cur and cur in names:
                    self._model_combo.set(cur)
                elif not cur:
                    self._ollama.select_best()
                    cur = self._ollama.get_current()
                    if cur: self._model_combo.set(cur)
            else:
                self._model_combo.configure(values=["(no models installed)"])
                self._model_combo.set("(no models installed)")
            # Render model list
            self._render_model_list(models)
        self._run_async(do, done)
