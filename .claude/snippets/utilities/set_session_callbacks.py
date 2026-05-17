# From: session_manager.py:197
# Wire UI callbacks to a session's executor.

    def set_session_callbacks(
        self,
        session_id: str,
        on_output: Optional[Callable] = None,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_tick: Optional[Callable] = None,
        on_status: Optional[Callable] = None,
    ) -> None:
        """Wire UI callbacks to a session's executor."""
        session = self._sessions.get(session_id)
        if session and session.executor:
            session.executor.set_callbacks(
                on_output=on_output,
                on_task_start=on_task_start,
                on_task_complete=on_task_complete,
                on_tick=on_tick,
                on_status=on_status,
            )
