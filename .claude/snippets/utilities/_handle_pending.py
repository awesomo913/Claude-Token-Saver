# From: claude_backend/gui.py:728
# Load a pending improve-request payload into the Builder tab.

    def _handle_pending(self, path: Path) -> None:
        """Load a pending improve-request payload into the Builder tab."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Pending file unreadable, deleting: %s", e)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            return

        # Always delete the pending file after reading — even if processing
        # fails — so we don't loop on a corrupt payload.
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

        if payload.get("kind") != "improve_request":
            return

        original = str(payload.get("original_prompt", "")).strip()
        project_path = str(payload.get("project_path", "")).strip()
        if not original:
            return

        # Switch to the picked project if different (and dir exists).
        if project_path and (not self._project_path or
                             str(self._project_path) != project_path):
            pp = Path(project_path)
            if pp.is_dir():
                self._auto_load_project(pp)

        # Switch to Builder view, populate request box, refresh preview.
        self._show_view("builder")
        try:
            self._request_box.delete("1.0", "end")
            self._request_box.insert("1.0", original)
            self._update_preview()
        except Exception as e:
            logger.exception("Pending populate failed: %s", e)

        # If the HTTP server auto-injected snippets, surface its pre-built
        # prompt directly in the preview so the user actually sees the
        # added code. _update_preview re-runs locally on any subsequent
        # user input, which is the right behavior — this is a one-shot
        # "here's what /improve produced" display.
        injected_n = int(payload.get("injected_snippets") or 0)
        injected_t = int(payload.get("injected_tokens") or 0)
        server_prompt = str(payload.get("improved_prompt") or "")
        if injected_n > 0 and server_prompt:
            try:
                self._preview.configure(state="normal")
                self._preview.delete("1.0", "end")
                self._preview.insert("1.0", server_prompt)
                self._preview.configure(state="disabled")
            except Exception as e:
                logger.debug("Preview override failed: %s", e)

        # Raise window to front so user sees Copy Prompt button.
        self._force_to_foreground()

        if injected_n > 0:
            self._toast(
                f"Auto-pulled {injected_n} snippet(s) ({injected_t} tokens)",
                "success",
            )
        else:
            self._toast("Loaded prompt from external trigger", "success")
        self._log(
            f"HTTP IPC: loaded prompt ({len(original)} chars); "
            f"injected_snippets={injected_n} tokens={injected_t}"
        )
