# From: claude_backend/prefs.py:27
# User-facing preferences. Add fields here; defaults always backfilled.

@dataclass
class Prefs:
    """User-facing preferences. Add fields here; defaults always backfilled."""
    show_welcome_on_launch: bool = True
    welcome_seen_count: int = 0
    last_project_path: str = ""
    show_tray_on_start: bool = False  # autostart hint, not enforced
    auto_launch_gui_on_session: bool = False  # opt-in: open GUI on Claude session
    auto_launch_minimized: bool = True  # if auto-launch on, prefer tray over window

    # ── HTTP backend (Phase 0) ────────────────────────────────────────
    http_port: int = 7321  # localhost-only HTTP API for browser ext / overlay / hotkey

    # ── Floating overlay button (Phase 2) ─────────────────────────────
    show_overlay: bool = False  # Win32 always-on-top "Improve & Copy" pill
    overlay_position: list = None  # type: ignore  # [x, y] screen coords; None = first-launch default

    # ── Global hotkey daemon (Phase 3) ────────────────────────────────
    enable_hotkey: bool = False
    hotkey_combo: str = "ctrl+shift+i"

    # ── Local AI (Ollama) auto-start ──────────────────────────────────
    # Spawns `ollama app.exe` at tray boot so downloaded models are
    # reachable after a reboot without the user manually launching
    # Ollama. Skipped silently if Ollama isn't installed.
    auto_start_ollama: bool = True

    def __post_init__(self) -> None:
        # Mutable defaults for dataclass fields must be created lazily.
        if self.overlay_position is None:
            self.overlay_position = [0, 0]

    @classmethod
    def load(cls) -> "Prefs":
        """Load prefs. Missing file or bad JSON -> defaults."""
        if not PREFS_PATH.is_file():
            return cls()
        try:
            data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("prefs load failed (%s); using defaults", e)
            return cls()
        if not isinstance(data, dict):
            return cls()
        # Filter to known fields only — forward-compat for new keys.
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in valid}
        try:
            return cls(**clean)
        except TypeError as e:
            logger.warning("prefs schema mismatch (%s); using defaults", e)
            return cls()

    def save(self) -> bool:
        """Persist prefs atomically. Returns True on success."""
        try:
            PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(asdict(self), indent=2)
            tmp = PREFS_PATH.with_suffix(PREFS_PATH.suffix + ".tmp")
            try:
                tmp.write_text(text, encoding="utf-8")
                os.replace(tmp, PREFS_PATH)
            except OSError:
                # Clean up temp file if rename failed.
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            return True
        except OSError as e:
            logger.warning("prefs save failed: %s", e)
            return False
