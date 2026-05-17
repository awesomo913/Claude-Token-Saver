# From: claude_backend/gui.py:3177
# Kill every other-process whose argv contains `arg` exactly.

    def _kill_processes_by_arg(self, arg: str) -> int:
        """Kill every other-process whose argv contains `arg` exactly.

        Returns count killed. Uses psutil to scope to ClaudeTokenSaver
        instances only — won't touch the GUI we're running in (filter
        excludes self_pid).
        """
        try:
            import psutil
        except ImportError:
            logger.warning("psutil unavailable; cannot scope kill")
            return 0
        import os as _os
        self_pid = _os.getpid()
        killed = 0
        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                if p.info.get("pid") == self_pid:
                    continue
                cmd = p.info.get("cmdline") or []
                if arg in cmd:
                    p.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue
        return killed
