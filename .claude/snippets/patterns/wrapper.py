# From: sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py:164

        def wrapper():
            try:
                fn()
            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_busy(False))
                self.root.after(0, self._refresh_status)
