# From: session_manager.py:75
# Create a new session in the given corner.

    def create_session(
        self,
        ai_profile: AIProfile,
        corner: str,
    ) -> Session:
        """Create a new session in the given corner."""
        if len(self._sessions) >= MAX_SESSIONS:
            raise RuntimeError(f"Maximum {MAX_SESSIONS} sessions reached")

        if corner in self._corner_map:
            raise RuntimeError(f"Corner {corner} already occupied")

        if corner not in CORNERS:
            raise RuntimeError(f"Invalid corner: {corner}. Use: {CORNERS}")

        # Create client
        client = UniversalBrowserClient(
            ai_profile=ai_profile,
            corner=corner,
            use_traffic_control=True,
        )

        # Create task queue with corner-specific persistence
        queue_path = get_config_dir() / f"task_queue_{corner.replace('-', '_')}.json"
        task_queue = TaskQueue(save_path=queue_path)

        # Create executor
        executor = TaskExecutor(client, task_queue)

        session = Session(
            ai_profile=ai_profile,
            corner=corner,
            client=client,
            task_queue=task_queue,
            executor=executor,
            is_active=True,
        )

        self._sessions[session.session_id] = session
        self._corner_map[corner] = session.session_id

        logger.info("Created session %s: %s at %s",
                     session.session_id, ai_profile.name, corner)
        return session
