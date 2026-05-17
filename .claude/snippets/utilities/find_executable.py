# From: claude_backend/ollama_manager.py:59
# Locate the Ollama tray binary so we can auto-start the daemon.

    @staticmethod
    def find_executable() -> Optional[Path]:
        """Locate the Ollama tray binary so we can auto-start the daemon.

        Preference order:
          1. `ollama app.exe` — Windows tray app; spawning it starts the
             daemon AND drops a tray icon the user can manage. Best UX.
          2. `ollama.exe` — CLI; we'd have to call `ollama serve` and
             keep the process. Less ideal but works as fallback.
          3. PATH lookup as a last resort.

        Returns None if Ollama isn't installed.
        """
        if sys.platform != "win32":
            cli = shutil.which("ollama")
            return Path(cli) if cli else None

        candidates = [
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs" / "Ollama" / "ollama app.exe",
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs" / "Ollama" / "ollama.exe",
            Path(r"C:\Program Files\Ollama\ollama app.exe"),
            Path(r"C:\Program Files\Ollama\ollama.exe"),
        ]
        for p in candidates:
            if p.is_file():
                return p
        on_path = shutil.which("ollama")
        return Path(on_path) if on_path else None
