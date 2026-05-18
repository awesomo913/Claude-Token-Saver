# From: broadcast.py:219
# Start broadcasting to all target sessions.

    def start(self, config: BroadcastConfig) -> None:
        """Start broadcasting to all target sessions."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._iteration_counts.clear()
        self._threads.clear()

        # Determine target sessions
        if config.session_ids:
            sessions = [
                self._sm.get_session(sid)
                for sid in config.session_ids
                if self._sm.get_session(sid)
            ]
        else:
            sessions = self._sm.active_sessions

        if not sessions:
            logger.warning("No active sessions to broadcast to")
            self._running = False
            return

        # Engineer the initial prompt
        engineered = engineer_prompt(
            task=config.task,
            build_target=config.build_target,
            enhancements=config.enhancements,
            context=config.context,
        )

        if self._on_status:
            names = ", ".join(s.ai_profile.name for s in sessions)
            self._on_status(f"Broadcasting to {len(sessions)} sessions: {names}")

        logger.info("Broadcasting to %d sessions: %s",
                     len(sessions),
                     [s.display_name for s in sessions])

        # Model switching is done manually by the user before broadcast.
        # Auto-switching was unreliable (typed model names into chat input).
        # The UI shows a reminder: "Pick a different model on each window first."

        # Smart routing: single orchestrated thread instead of per-session
        if config.smart_route and SMART_ROUTER_AVAILABLE:
            t = threading.Thread(
                target=self._smart_route_loop,
                args=(sessions, config, engineered),
                daemon=True,
            )
            self._threads.append(t)
            t.start()
            return

        # Launch a thread per session
        for session in sessions:
            if not session.is_configured:
                logger.warning("Skipping unconfigured session: %s", session.display_name)
                continue

            t = threading.Thread(
                target=self._session_loop,
                args=(session, config, engineered),
                daemon=True,
            )
            self._threads.append(t)
            t.start()
