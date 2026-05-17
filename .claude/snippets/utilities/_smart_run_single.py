# From: broadcast.py:591
# Send a prompt to a single session (used by smart routing).

    def _smart_run_single(
        self, session, config: BroadcastConfig, prompt: str,
        label: str, start_time: float
    ) -> None:
        """Send a prompt to a single session (used by smart routing)."""
        sid = session.session_id
        ai_name = session.ai_profile.name

        if self._on_output:
            self._on_output(sid, "system",
                f"[{ai_name}] SmartRoute → {label}\n{'='*50}\n")

        result = session.client.generate(
            prompt=prompt,
            system_instruction="Complete the task directly with clean, working code.",
            on_progress=lambda t, s=sid: (
                self._on_output(s, "code", t) if self._on_output else None),
        )
        self._results[sid] = result
        self._save_result(session, config.task, 1,
                          f"SmartRoute_{label}", result, start_time)
        if self._on_output:
            self._on_output(sid, "result", result)
