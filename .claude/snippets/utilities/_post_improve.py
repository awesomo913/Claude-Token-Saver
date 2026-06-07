# From: claude_backend/overlay.py:672
# POST to /improve. The GUI picks up the result via pending file.

    def _post_improve(
        self, prompt: str, project_path: str, saved_clipboard: str,
    ) -> None:
        """POST to /improve. The GUI picks up the result via pending file.

        We deliberately do NOT call AllowSetForegroundWindow here even
        though the overlay process is foreground-eligible. The grant is
        time-limited by Windows (expires on next user input, ~1s), and
        urlopen + the GUI's pending-file poll loop can take longer than
        that. The tray's HTTP handler does the grant right before
        spawning/signaling the GUI in http_server.py — that's the right
        moment.
        """
        error: str = ""
        try:
            body = json.dumps({
                "prompt": prompt, "project_path": project_path,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{self._prefs.http_port}/improve",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                _ = r.read()
        except Exception as e:
            error = type(e).__name__ + (f": {e}" if str(e) else "")
            logger.warning("Overlay /improve POST failed: %s", error)
        finally:
            # Restore original clipboard if any (best-effort).
            if pyperclip is not None and saved_clipboard:
                try:
                    pyperclip.copy(saved_clipboard)
                except Exception:
                    pass
        # Schedule the user-visible error on the Tk main thread. Without
        # this the overlay silently swallows network failures and the
        # user thinks Improve is broken.
        if error:
            try:
                self.after(0, lambda msg=error: self._show_error_toast(msg))
            except Exception as e:
                logger.debug("error toast schedule failed: %s", e)
