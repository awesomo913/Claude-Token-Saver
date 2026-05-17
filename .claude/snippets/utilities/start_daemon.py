# From: claude_backend/ollama_manager.py:90
# Spawn the Ollama daemon if installed, and wait until reachable.

    def start_daemon(self, wait_seconds: float = 8.0) -> bool:
        """Spawn the Ollama daemon if installed, and wait until reachable.

        Idempotent: returns True immediately if `is_running()` already.
        Returns False if Ollama isn't installed or didn't come up within
        `wait_seconds` (poll every 250ms).

        Detached spawn so closing Token Saver doesn't kill the daemon —
        users may want Ollama to keep running for other apps.
        """
        if self.is_running():
            return True
        exe = self.find_executable()
        if exe is None:
            logger.info("Ollama not installed — auto-start skipped.")
            return False
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = (subprocess.CREATE_NO_WINDOW
                                 | subprocess.DETACHED_PROCESS)
            args: list[str] = [str(exe)]
            if exe.name.lower() == "ollama.exe":
                # Plain CLI — explicitly start the server.
                args.append("serve")
            subprocess.Popen(
                args, creationflags=creationflags, close_fds=True,
                cwd=str(exe.parent),
            )
        except OSError as e:
            logger.warning("Ollama spawn failed (%s): %s", exe, e)
            return False

        # Poll until reachable or timeout.
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if self.is_running():
                logger.info("Ollama daemon is up (started via %s).", exe.name)
                return True
            time.sleep(0.25)
        logger.warning("Ollama daemon did not respond within %.1fs.",
                       wait_seconds)
        return False
