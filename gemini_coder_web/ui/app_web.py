"""Autocoder - Universal multi-session browser AI automation.

Manages up to 4 AI sessions simultaneously (Gemini, ChatGPT, Claude,
Ollama, OpenRouter, or any AI with a browser/window chat interface).
Each session gets a corner of the screen and its own task queue.

Broadcast Mode: Send one task to ALL sessions, loop improvements endlessly.
Prompt Architect integration: Tasks auto-engineered into production prompts.
"""

import customtkinter as ctk
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

from gemini_coder import __version__ as base_version
from ..bridge import GUIBridge
from gemini_coder.config import ConfigManager
from gemini_coder.task_manager import TaskQueue, TaskExecutor, CodingTask, TaskStatus
from gemini_coder.expander import ExpansionEngine
from gemini_coder.history import HistoryManager
from gemini_coder.platform_utils import detect_platform, get_config_dir
from gemini_coder.ui.theme import get_colors, SPACING, ICONS
from gemini_coder.ui.app import GeminiCoderApp, StatusBar, ToastNotification

from .. import __version__, __app_name__
from ..ai_profiles import AIProfile, PRESET_PROFILES, get_profile_names, get_profile
from ..session_manager import SessionManager, Session, CORNERS
from ..auto_save import save_task_output
from ..broadcast import BroadcastController, BroadcastConfig, engineer_prompt, PROMPT_ENGINE_AVAILABLE
from ..window_manager import (
    list_candidate_windows, get_foreground_window,
    get_window_title, capture_foreground_and_position,
)
from ..cdp_client import (
    is_cdp_available, discover_cdp_targets,
    launch_chrome_with_cdp, DEFAULT_CDP_PORT,
    CDP_CORNER_PORTS, get_cdp_port_for_corner,
    is_chrome_running, kill_chrome,
)

try:
    from mousetraffic.client import TrafficClient
    TRAFFIC_AVAILABLE = True
except ImportError:
    TRAFFIC_AVAILABLE = False

logger = logging.getLogger(__name__)

# Corner display labels
CORNER_LABELS = {
    "top-left": "Top-Left",
    "top-right": "Top-Right",
    "bottom-left": "Bot-Left",
    "bottom-right": "Bot-Right",
}


class SessionCard(ctk.CTkFrame):
    """UI card for one AI session slot (one corner of the screen)."""

    def __init__(self, parent, corner: str, colors: dict, app, **kwargs):
        super().__init__(parent, fg_color=colors["bg_card"], corner_radius=8,
                         border_width=1, border_color=colors["border"], **kwargs)
        self._corner = corner
        self._colors = colors
        self._app = app
        self._session: Session = None

        c = colors
        label = CORNER_LABELS.get(corner, corner)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        self._dot = ctk.CTkLabel(header, text="\u25CF", font=("Segoe UI", 14),
                                  text_color=c["fg_muted"])
        self._dot.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(header, text=label, font=("Segoe UI", 12, "bold"),
                      text_color=c["fg_heading"]).pack(side="left")

        self._status_label = ctk.CTkLabel(header, text="Empty",
                                           font=("Segoe UI", 10),
                                           text_color=c["fg_muted"])
        self._status_label.pack(side="right")

        # AI selector
        ai_row = ctk.CTkFrame(self, fg_color="transparent")
        ai_row.pack(fill="x", padx=8, pady=2)

        ctk.CTkLabel(ai_row, text="AI:", font=("Segoe UI", 11),
                      text_color=c["fg_secondary"]).pack(side="left")

        self._ai_selector = ctk.CTkComboBox(
            ai_row, values=get_profile_names(),
            font=("Segoe UI", 11), width=140,
            fg_color=c["bg_input"], text_color=c["fg_primary"],
            border_color=c["border"],
        )
        self._ai_selector.pack(side="left", padx=4)
        self._ai_selector.set("Gemini")

        # Window picker - list available windows
        pick_row = ctk.CTkFrame(self, fg_color="transparent")
        pick_row.pack(fill="x", padx=8, pady=2)

        self._window_picker = ctk.CTkComboBox(
            pick_row, values=["(click Refresh)"],
            font=("Segoe UI", 10), width=180, height=24,
            fg_color=c["bg_input"], text_color=c["fg_primary"],
            border_color=c["border"],
        )
        self._window_picker.pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            pick_row, text="\u21BB", font=("Segoe UI", 11),
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["fg_secondary"], height=24, width=28,
            command=self._refresh_window_list,
        ).pack(side="left")

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(2, 8))

        self._capture_btn = ctk.CTkButton(
            btn_row, text="Grab", font=("Segoe UI", 11, "bold"),
            fg_color="#8e44ad", hover_color="#9b59b6",
            height=28, width=55,
            command=self._on_capture,
        )
        self._capture_btn.pack(side="left", padx=1)

        self._launch_btn = ctk.CTkButton(
            btn_row, text="Launch", font=("Segoe UI", 11, "bold"),
            fg_color=c["accent"], hover_color=c["accent_hover"],
            height=28, width=60,
            command=self._on_launch,
        )
        self._launch_btn.pack(side="left", padx=1)

        # Quick create session button (bridges to backend via GUIBridge)
        self._create_session_btn = ctk.CTkButton(
            btn_row, text="Create", font=("Segoe UI", 11, "bold"),
            fg_color=c["accent"], hover_color=c["accent_hover"],
            height=28, width=60,
            command=self._on_create_session,
        )
        self._create_session_btn.pack(side="left", padx=1)

        self._start_btn = ctk.CTkButton(
            btn_row, text=f"{ICONS['play']}", font=("Segoe UI", 11, "bold"),
            fg_color=c["success"], hover_color="#27ae60",
            height=28, width=35, state="disabled",
            command=self._on_start,
        )
        self._start_btn.pack(side="left", padx=1)

        self._stop_btn = ctk.CTkButton(
            btn_row, text=f"{ICONS['stop']}", font=("Segoe UI", 11, "bold"),
            fg_color=c["error"],
            height=28, width=35, state="disabled",
            command=self._on_stop,
        )
        self._stop_btn.pack(side="left", padx=1)

        self._remove_btn = ctk.CTkButton(
            btn_row, text="X", font=("Segoe UI", 10),
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["error"], height=28, width=28,
            command=self._on_remove,
        )
        self._remove_btn.pack(side="right")

        # CDP mode indicator
        self._mode_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 9),
                                          text_color=c["fg_muted"])
        self._mode_label.pack(fill="x", padx=8, pady=(0, 4))

        # Window handle tracking
        self._window_handles: dict[str, int] = {}  # display_name -> hwnd
        self._task_text: str = ""  # Current task status text

    def _refresh_window_list(self) -> None:
        """Populate the window picker with available windows.

        Shows CDP tabs first (preferred), then pyautogui windows as fallback.
        """
        from ..universal_client import UniversalBrowserClient

        self._window_handles.clear()
        self._cdp_targets: dict[str, object] = {}  # display -> CDPTarget
        values = []

        # ── CDP targets first (preferred) — scan all ports ────
        seen_target_ids = set()
        try:
            for port in sorted(set(CDP_CORNER_PORTS.values())):
                cdp_targets = discover_cdp_targets(port)
                for target in cdp_targets:
                    if target.target_id in seen_target_ids:
                        continue
                    seen_target_ids.add(target.target_id)
                    if not target.title or len(target.title) < 3:
                        continue
                    if target.url.startswith("chrome://") or target.url == "about:blank":
                        continue
                    short = target.title[:45]
                    display = f"\U0001F310 {short}"
                    self._cdp_targets[display] = target
                    values.append(display)
        except Exception:
            pass

        # ── Pyautogui windows (fallback) ───────────────────────
        candidates = list_candidate_windows()
        with UniversalBrowserClient._claimed_lock:
            claimed = set(UniversalBrowserClient._claimed_hwnds)

        try:
            app_hwnd = self._app.winfo_id()
        except Exception:
            app_hwnd = None

        for hwnd, cls, title in candidates:
            if hwnd in claimed:
                continue
            if app_hwnd and hwnd == app_hwnd:
                continue
            if "autocoder" in title.lower():
                continue
            short = title[:45]
            display = f"[{hwnd}] {short}"
            self._window_handles[display] = hwnd
            values.append(display)

        if values:
            self._window_picker.configure(values=values)
            self._window_picker.set(values[0])
        else:
            self._window_picker.configure(values=["(no windows found)"])
            self._window_picker.set("(no windows found)")

    def _on_create_session(self) -> None:
        """Create a new backend session for this corner via the GUI bridge."""
        if not hasattr(self._app, "_bridge") or self._app._bridge is None:
            self._app._toast("Bridge not available", "warning")
            return
        sid = self._app._bridge.create_session(self._ai_selector.get(), self._corner)
        if sid:
            self._app._toast(f"Session created: {sid}", "success")
            sess = self._app.session_mgr.get_session(sid)
            if sess:
                self._app._activate_session(sess)
            self._app._refresh_all_window_lists()
            self._app._update_assign_selector()
        else:
            self._app._toast("Failed to create session", "error")

    def _ensure_session(self) -> bool:
        """Create session for this corner if it doesn't exist yet. Returns True on success."""
        if self._session:
            return True
        ai_name = self._ai_selector.get()
        profile = get_profile(ai_name)
        try:
            self._session = self._app.session_mgr.create_session(profile, self._corner)
            self._wire_callbacks()
            self._app._activate_session(self._session)
            return True
        except RuntimeError as e:
            self._app._toast(str(e), "error")
            return False

    def _on_capture(self) -> None:
        """Capture the selected window from the picker dropdown."""
        selection = self._window_picker.get()

        # Check if it's a CDP target (starts with globe emoji)
        cdp_target = getattr(self, '_cdp_targets', {}).get(selection)
        hwnd = self._window_handles.get(selection)

        if not cdp_target and not hwnd:
            # Auto-refresh if dropdown is empty/stale
            self._refresh_window_list()
            selection = self._window_picker.get()
            cdp_target = getattr(self, '_cdp_targets', {}).get(selection)
            hwnd = self._window_handles.get(selection)

        if not cdp_target and not hwnd:
            self._app._toast("No windows found. Open a browser/terminal first.", "warning")
            return

        ai_name = self._ai_selector.get()
        profile = get_profile(ai_name)

        if not self._ensure_session():
            return

        self._session.ai_profile = profile
        if self._session.client:
            self._session.client.profile = profile

        if cdp_target:
            # CDP target — connect directly via CDP
            self._capture_btn.configure(state="disabled", text="...")
            self._status_label.configure(text="Connecting CDP...", text_color=self._colors["info"])

            def cdp_worker():
                from ..cdp_client import CDPConnection, CDPChatAutomation, get_selectors_for_profile
                try:
                    conn = CDPConnection(cdp_target.ws_url)
                    if conn.connect():
                        selectors = get_selectors_for_profile(ai_name)
                        automation = CDPChatAutomation(conn, selectors, ai_name)
                        # Attach to the client
                        client = self._session.client
                        client._cdp = automation
                        client._cdp_available = True
                        client._configured = True
                        self._session.is_configured = True

                        self.after(0, lambda: self._set_state("ready"))
                        self.after(0, lambda: self._mode_label.configure(
                            text="Mode: CDP (reliable)", text_color=self._colors["success"]))
                        self.after(0, lambda: self._app._toast(
                            f"CDP connected: {cdp_target.title[:35]} -> {CORNER_LABELS[self._corner]}", "success"))
                        self.after(0, self._app._update_assign_selector)
                        self.after(0, self._app._refresh_all_window_lists)
                    else:
                        self.after(0, lambda: self._set_state("error"))
                        self.after(0, lambda: self._app._toast("CDP connection failed", "error"))
                except Exception as e:
                    self.after(0, lambda: self._set_state("error"))
                    self.after(0, lambda: self._app._toast(f"CDP error: {e}", "error"))

            threading.Thread(target=cdp_worker, daemon=True).start()
        else:
            # Pyautogui fallback — window handle
            ok = self._app.session_mgr.capture_window_for_session(
                self._session.session_id, hwnd
            )
            if ok:
                title = get_window_title(hwnd)
                self._set_state("ready")
                if self._session.client and self._session.client.using_cdp:
                    self._mode_label.configure(text="Mode: CDP (reliable)", text_color=self._colors["success"])
                    self._app._toast(f"Grabbed via CDP: {title[:35]} -> {CORNER_LABELS[self._corner]}", "success")
                else:
                    self._mode_label.configure(text="Mode: pyautogui (fallback)", text_color=self._colors["warning"])
                    self._app._toast(f"Grabbed: {title[:35]} -> {CORNER_LABELS[self._corner]}", "success")
                self._app._update_assign_selector()
                self._app._refresh_all_window_lists()
            else:
                self._app._toast("Failed to capture window", "error")

    def _on_launch(self) -> None:
        ai_name = self._ai_selector.get()
        profile = get_profile(ai_name)

        if not self._ensure_session():
            return

        self._session.ai_profile = profile
        if self._session.client:
            self._session.client.profile = profile

        self._launch_btn.configure(state="disabled", text="...")
        self._status_label.configure(text="Launching...", text_color=self._colors["info"])

        def worker():
            ok = self._app.session_mgr.configure_session(self._session.session_id)
            if ok:
                self.after(0, lambda: self._set_state("ready"))
                # Show CDP vs pyautogui mode
                cdp = self._session.client and self._session.client.using_cdp
                mode = "CDP" if cdp else "pyautogui"
                self.after(0, lambda: self._mode_label.configure(
                    text=f"Mode: {mode}" + (" (reliable)" if cdp else " (fallback)"),
                    text_color=self._colors["success"] if cdp else self._colors["warning"],
                ))
                self.after(0, lambda: self._app._toast(
                    f"{profile.name} ready [{mode}] at {CORNER_LABELS[self._corner]}", "success"))
                self.after(0, self._app._update_assign_selector)
            else:
                self.after(0, lambda: self._set_state("error"))
                self.after(0, lambda: self._app._toast(
                    f"Failed to find {profile.name} window", "error"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_start(self) -> None:
        if self._session:
            ok = self._app.session_mgr.start_session(self._session.session_id)
            if ok:
                self._set_state("running")
            else:
                self._app._toast("No tasks in queue or not configured", "warning")

    def _on_stop(self) -> None:
        if self._session:
            self._app.session_mgr.stop_session(self._session.session_id)
            self._set_state("ready")

    def _on_remove(self) -> None:
        if self._session:
            self._app.session_mgr.remove_session(self._session.session_id)
            self._session = None
        self._set_state("empty")

    def _wire_callbacks(self) -> None:
        if not self._session:
            return
        sid = self._session.session_id

        def on_output(kind, text):
            self._app._on_session_output(sid, kind, text)

        def on_task_start(task):
            self.after(0, lambda: self._set_state("running"))
            self._app._on_session_task_start(sid, task)

        def on_task_complete(task):
            self._app._on_session_task_complete(sid, task)
            # Check if more tasks pending
            if self._session and self._session.task_queue:
                if self._session.task_queue.pending_tasks:
                    self.after(0, lambda: self._set_state("running"))
                else:
                    self.after(0, lambda: self._set_state("ready"))

        def on_tick(task):
            self._app._on_session_tick(sid, task)

        def on_status(status, detail):
            self._app._on_session_status(sid, status, detail)

        self._app.session_mgr.set_session_callbacks(
            sid,
            on_output=on_output,
            on_task_start=on_task_start,
            on_task_complete=on_task_complete,
            on_tick=on_tick,
            on_status=on_status,
        )

    def _set_state(self, state: str) -> None:
        c = self._colors
        if state == "empty":
            self._dot.configure(text_color=c["fg_muted"])
            self._status_label.configure(text="Empty", text_color=c["fg_muted"])
            self._launch_btn.configure(state="normal", text="Launch")
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="disabled")
            self._ai_selector.configure(state="normal")
        elif state == "ready":
            self._dot.configure(text_color=c["success"])
            ai = self._session.ai_profile.name if self._session else "?"
            self._status_label.configure(text=f"{ai} Ready", text_color=c["success"])
            self._launch_btn.configure(state="normal", text="Relaunch")
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")
        elif state == "running":
            self._dot.configure(text_color=c["warning"])
            self._status_label.configure(text=self._task_text or "Running...", text_color=c["warning"])
            self._launch_btn.configure(state="disabled")
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
        elif state == "error":
            self._dot.configure(text_color=c["error"])
            self._status_label.configure(text="Error", text_color=c["error"])
            self._launch_btn.configure(state="normal", text="Retry")
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="disabled")

    @property
    def session(self) -> Session:
        return self._session


class GeminiCoderWebApp(GeminiCoderApp):
    """AI Browser Coder - multi-session universal AI automation."""

    def __init__(self) -> None:
        print("DEBUG: Calling super().__init__()")
        super().__init__()
        print("DEBUG: Super init completed")
        print(f"DEBUG: _content exists: {hasattr(self, '_content')}")
        if hasattr(self, '_content'):
            print(f"DEBUG: _content type: {type(self._content)}")
        # Initialize global sessions store for the new Global Create panel
        self._global_sessions = {}

        self._start_time = time.time()
        self._config_manager = ConfigManager()
        self._cfg = self._config_manager.config
        self._platform = detect_platform()

        ctk.set_appearance_mode(self._cfg.theme)
        ctk.set_default_color_theme("blue")
        self._colors = get_colors(self._cfg.theme)

        self.title(f"{__app_name__} v{__version__}")
        self.geometry(f"{self._cfg.window_width}x{self._cfg.window_height}")
        self.minsize(1000, 650)

        # ── Session manager (replaces single client) ─────────────
        # Clear any stale claimed hwnds from a previous run
        from ..universal_client import UniversalBrowserClient
        UniversalBrowserClient._claimed_hwnds.clear()

        self.session_mgr = SessionManager()

        # No default session — session cards handle creation.
        # Base class references self._gemini, so use a stub with is_configured=False.
        class _Stub:
            is_configured = False
            def cancel(self): pass
            def update_settings(self, **kw): pass
        self._gemini = _Stub()
        self._task_queue = TaskQueue()  # Empty queue until a session is selected
        self._task_executor = None
        self._expander = None  # Created when first session connects
        self._history = HistoryManager()
        # Bridge to connect GUI with backend logic
        self._bridge = GUIBridge(self.session_mgr, self._history, None)

        # Track active session for output display
        self._active_session_id = None
        self._session_outputs: dict[str, str] = {}  # session_id -> latest output

        self._current_view = "expand"
        self._last_completed_task = None
        self._session_cards: dict[str, SessionCard] = {}
        self._broadcast = BroadcastController(self.session_mgr)
        self._broadcast.set_callbacks(
            on_output=lambda sid, kind, text: self._on_session_output(sid, kind, text),
            on_status=lambda msg: self.after(0, lambda: self._bc_status.configure(text=msg)),
            on_iteration=self._on_broadcast_iteration,
        )

        self._setup_logging()
        self._build_ui()
        self._bind_shortcuts()
        self._setup_callbacks()
        self._start_clock()

        self.after(500, lambda: self._show_view("settings"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Settings view with session management ─────────────────────

    def _build_settings_view(self) -> None:
        c = self._colors
        frame = ctk.CTkFrame(self._content, fg_color=c["bg_primary"], corner_radius=0)
        self._frames["settings"] = frame

        scroll = ctk.CTkScrollableFrame(frame, fg_color=c["bg_primary"])
        scroll.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["md"])

        ctk.CTkLabel(
            scroll, text=f"{ICONS['gear']} AI Browser Coder - Sessions",
            font=("Segoe UI", 20, "bold"),
            text_color=c["fg_heading"],
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            scroll,
            text="Control up to 4 AI windows simultaneously. Each gets a corner of your screen.",
            font=("Segoe UI", 12),
            text_color=c["fg_secondary"],
        ).pack(anchor="w", pady=(0, SPACING["md"]))

        # ── SESSION GRID (2x2) ───────────────────────────────────
        session_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        session_frame.pack(fill="x", pady=SPACING["sm"])

        # Top row
        top_row = ctk.CTkFrame(session_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=2)

        card_tl = SessionCard(top_row, "top-left", c, self)
        card_tl.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._session_cards["top-left"] = card_tl

        card_tr = SessionCard(top_row, "top-right", c, self)
        card_tr.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._session_cards["top-right"] = card_tr

        # Bottom row
        bot_row = ctk.CTkFrame(session_frame, fg_color="transparent")
        bot_row.pack(fill="x", pady=2)

        card_bl = SessionCard(bot_row, "bottom-left", c, self)
        card_bl.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._session_cards["bottom-left"] = card_bl

        card_br = SessionCard(bot_row, "bottom-right", c, self)
        card_br.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._session_cards["bottom-right"] = card_br

        # ── TASK ASSIGNMENT ──────────────────────────────────────
        assign_card = ctk.CTkFrame(scroll, fg_color=c["bg_card"], corner_radius=8)
        assign_card.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            assign_card, text=f"{ICONS['tasks']} Assign Tasks to Sessions",
            font=("Segoe UI", 15, "bold"),
            text_color=c["fg_heading"],
        ).pack(padx=SPACING["lg"], pady=(SPACING["md"], 4), anchor="w")

        ctk.CTkLabel(
            assign_card, text=(
                "When you add a task in the Task Queue view, it goes to the "
                "selected session below."
            ),
            font=("Segoe UI", 11),
            text_color=c["fg_muted"],
            wraplength=650, justify="left",
        ).pack(padx=SPACING["lg"], pady=(0, SPACING["sm"]), anchor="w")

        assign_row = ctk.CTkFrame(assign_card, fg_color="transparent")
        assign_row.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["md"]))

        ctk.CTkLabel(assign_row, text="Send tasks to:",
                      font=("Segoe UI", 12, "bold"),
                      text_color=c["fg_primary"]).pack(side="left")

        self._assign_selector = ctk.CTkComboBox(
            assign_row, values=["(no sessions yet)"],
            font=("Segoe UI", 11), width=250,
            fg_color=c["bg_input"], text_color=c["fg_primary"],
            border_color=c["border"],
            command=self._on_assign_change,
        )
        self._assign_selector.pack(side="left", padx=SPACING["sm"])

        # ── BROADCAST MODE (Endless Loop) ────────────────────────
        bc_card = ctk.CTkFrame(scroll, fg_color=c["bg_tertiary"], corner_radius=8,
                                border_color="#8e44ad", border_width=2)
        bc_card.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            bc_card, text="\u26A1 Broadcast Mode — Endless Auto-Coding",
            font=("Segoe UI", 15, "bold"),
            text_color=c["fg_heading"],
        ).pack(padx=SPACING["lg"], pady=(SPACING["md"], 4), anchor="w")

        engine_tag = " (Prompt Architect active)" if PROMPT_ENGINE_AVAILABLE else " (raw prompts)"
        ctk.CTkLabel(
            bc_card, text=(
                "Type ONE task. It gets engineered into a production prompt" + engine_tag + ",\n"
                "then broadcast to ALL active sessions. Each session builds the code,\n"
                "then endlessly improves it until you click Stop.\n"
                "TIP: Pick a different free model on each OpenRouter window first!\n"
                "Output auto-saved to Downloads as labeled .txt files per session."
            ),
            font=("Segoe UI", 11),
            text_color=c["fg_muted"],
            wraplength=650, justify="left",
        ).pack(padx=SPACING["lg"], pady=(0, SPACING["sm"]), anchor="w")

        # Task input
        self._bc_task_input = ctk.CTkTextbox(
            bc_card, height=60, font=("Segoe UI", 12),
            fg_color=c["bg_input"], text_color=c["fg_primary"],
            border_color=c["border"], border_width=1, corner_radius=8,
        )
        self._bc_task_input.pack(fill="x", padx=SPACING["lg"], pady=4)
        self._bc_task_input.insert("1.0", "e.g., Build a calculator with history and themes")

        # Build target selector
        bt_row = ctk.CTkFrame(bc_card, fg_color="transparent")
        bt_row.pack(fill="x", padx=SPACING["lg"], pady=4)

        ctk.CTkLabel(bt_row, text="Build target:",
                      font=("Segoe UI", 11, "bold"),
                      text_color=c["fg_primary"]).pack(side="left")

        bt_values = ["PC Desktop App", "Website / Web App", "Game",
                     "Raspberry Pi App", "Android App", "Cross-Platform (PC + Pi)"]
        self._bc_build_target = ctk.CTkComboBox(
            bt_row, values=bt_values,
            font=("Segoe UI", 11), width=200,
            fg_color=c["bg_input"], text_color=c["fg_primary"],
            border_color=c["border"],
        )
        self._bc_build_target.pack(side="left", padx=SPACING["sm"])
        self._bc_build_target.set("PC Desktop App")

        # Buttons
        bc_btn_row = ctk.CTkFrame(bc_card, fg_color="transparent")
        bc_btn_row.pack(fill="x", padx=SPACING["lg"], pady=(4, SPACING["md"]))

        self._bc_start_btn = ctk.CTkButton(
            bc_btn_row, text="\u26A1 Broadcast to All",
            font=("Segoe UI", 14, "bold"),
            fg_color="#8e44ad", hover_color="#9b59b6",
            height=40,
            command=self._on_broadcast_start,
        )
        self._bc_start_btn.pack(side="left", padx=(0, 4))

        self._bc_stop_btn = ctk.CTkButton(
            bc_btn_row, text=f"{ICONS['stop']} Stop All (Ctrl+K)",
            font=("Segoe UI", 13, "bold"),
            fg_color=c["error"],
            height=40, state="disabled",
            command=self._on_broadcast_stop,
        )
        self._bc_stop_btn.pack(side="left", padx=4)

        self._bc_save_btn = ctk.CTkButton(
            bc_btn_row, text="\U0001F4BE Save All",
            font=("Segoe UI", 13, "bold"),
            fg_color=c["success"], hover_color="#27ae60",
            height=40,
            command=self._on_broadcast_save,
        )
        self._bc_save_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            bc_btn_row, text="\U0001F4C2 Open Downloads",
            font=("Segoe UI", 11),
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["fg_secondary"], height=36,
            command=lambda: subprocess.Popen(
                ["explorer", str(Path.home() / "Downloads")]),
        ).pack(side="left", padx=4)

        self._bc_status = ctk.CTkLabel(
            bc_btn_row, text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#8e44ad",
        )
        self._bc_status.pack(side="left", padx=SPACING["sm"])

        # ── CDP BROWSER AUTOMATION ────────────────────────────────
        cdp_card = ctk.CTkFrame(scroll, fg_color=c["bg_card"], corner_radius=8,
                                 border_color=c["success"], border_width=2)
        cdp_card.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            cdp_card, text="\U0001F310 CDP Browser Automation (Recommended)",
            font=("Segoe UI", 15, "bold"),
            text_color=c["fg_heading"],
        ).pack(padx=SPACING["lg"], pady=(SPACING["md"], 4), anchor="w")

        ctk.CTkLabel(
            cdp_card, text=(
                "CDP connects directly to Chrome's DOM — no blind clicking!\n"
                "It finds elements by CSS selector, types text directly, and reads\n"
                "responses from specific HTML elements. Much more reliable than pyautogui.\n\n"
                "Click 'Launch CDP Browser' to open a dedicated Autocoder Chrome.\n"
                "Log in to your AI sites ONCE — logins are remembered.\n"
                "Then Grab each AI tab in the session cards above."
            ),
            font=("Segoe UI", 11),
            text_color=c["fg_muted"],
            wraplength=650, justify="left",
        ).pack(padx=SPACING["lg"], pady=(0, SPACING["sm"]), anchor="w")

        cdp_btn_row = ctk.CTkFrame(cdp_card, fg_color="transparent")
        cdp_btn_row.pack(fill="x", padx=SPACING["lg"], pady=(0, 4))

        ctk.CTkButton(
            cdp_btn_row, text="\U0001F310 Launch CDP Browser",
            font=("Segoe UI", 13, "bold"),
            fg_color=c["success"], hover_color="#27ae60", height=38,
            command=self._on_launch_cdp_browser,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            cdp_btn_row, text="Check CDP",
            font=("Segoe UI", 11),
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["fg_secondary"], height=30,
            command=self._on_check_cdp,
        ).pack(side="left", padx=SPACING["sm"])

        self._cdp_status = ctk.CTkLabel(
            cdp_card, text="",
            font=("Segoe UI", 11), text_color=c["fg_muted"],
        )
        self._cdp_status.pack(padx=SPACING["lg"], pady=(0, SPACING["md"]), anchor="w")

        # ── TRAFFIC CONTROLLER ───────────────────────────────────
        traffic_card = ctk.CTkFrame(scroll, fg_color=c["bg_card"], corner_radius=8)
        traffic_card.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            traffic_card, text="\U0001F6A6 Mouse Traffic Controller",
            font=("Segoe UI", 15, "bold"),
            text_color=c["fg_heading"],
        ).pack(padx=SPACING["lg"], pady=(SPACING["md"], 4), anchor="w")

        ctk.CTkLabel(
            traffic_card, text=(
                "The Traffic Controller makes AI sessions take turns with the mouse.\n"
                "Start it before running multiple sessions. It also detects when YOU\n"
                "use the mouse and pauses bots until you're done (10s idle or top-right corner)."
            ),
            font=("Segoe UI", 11),
            text_color=c["fg_muted"],
            wraplength=650, justify="left",
        ).pack(padx=SPACING["lg"], pady=(0, SPACING["sm"]), anchor="w")

        traffic_btn_row = ctk.CTkFrame(traffic_card, fg_color="transparent")
        traffic_btn_row.pack(fill="x", padx=SPACING["lg"], pady=(0, 4))

        ctk.CTkButton(
            traffic_btn_row, text="\U0001F6A6 Start Traffic Controller",
            font=("Segoe UI", 13, "bold"),
            fg_color=c["success"], height=38,
            command=self._on_start_traffic,
        ).pack(side="left")

        ctk.CTkButton(
            traffic_btn_row, text="Check Status",
            font=("Segoe UI", 11),
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["fg_secondary"], height=30,
            command=self._on_check_traffic,
        ).pack(side="left", padx=SPACING["sm"])

        self._traffic_status = ctk.CTkLabel(
            traffic_card, text="",
            font=("Segoe UI", 11), text_color=c["fg_muted"],
        )
        self._traffic_status.pack(padx=SPACING["lg"], pady=(0, SPACING["md"]), anchor="w")

        # ── KEYBOARD SHORTCUTS ───────────────────────────────────
        kb_card = ctk.CTkFrame(scroll, fg_color=c["bg_card"], corner_radius=8)
        kb_card.pack(fill="x", pady=SPACING["sm"])

        ctk.CTkLabel(
            kb_card, text="\u2328 Keyboard Shortcuts",
            font=("Segoe UI", 15, "bold"),
            text_color=c["fg_heading"],
        ).pack(padx=SPACING["lg"], pady=(SPACING["md"], 4), anchor="w")

        ctk.CTkLabel(
            kb_card, text=(
                "  Ctrl + 1    Explore Mode\n"
                "  Ctrl + 2    Task Queue\n"
                "  Ctrl + 3    Settings / Sessions\n"
                "  Ctrl + K    KILL all sessions\n"
                "  Ctrl + R    Resume after kill\n"
                "  Esc         Stop current session\n"
                "  Ctrl + Q    Quit"
            ),
            font=("Consolas", 12),
            text_color=c["fg_secondary"],
            justify="left", anchor="w",
        ).pack(padx=SPACING["lg"], pady=(0, SPACING["md"]), anchor="w")

    # ── Override base-class setup that assumes a single executor ────

    def _setup_callbacks(self) -> None:
        """No-op: session cards wire their own callbacks via _wire_callbacks()."""
        self._task_queue.on_change(lambda: self.after(0, self._refresh_task_list))

    # ── Activate a session (set it as current for base-class refs) ──

    def _activate_session(self, session: Session) -> None:
        """Make a session the 'active' one for task queue, output, etc."""
        self._active_session_id = session.session_id
        self._task_queue = session.task_queue
        self._task_executor = session.executor
        if session.client:
            self._gemini = session.client
            if not self._expander:
                self._expander = ExpansionEngine(
                    self._gemini, depth_limit=self._cfg.expand_depth_limit
                )

    # ── Session callbacks ─────────────────────────────────────────

    def _on_session_output(self, session_id: str, kind: str, text: str) -> None:
        # Always store the latest text for display; "result" type is the actual AI output
        self._session_outputs[session_id] = text
        if session_id == self._active_session_id:
            def update():
                self._task_output.delete("1.0", "end")
                self._task_output.insert("1.0", text)
                if self._cfg.auto_scroll:
                    self._task_output.see("end")
            self.after(0, update)

    def _on_session_task_start(self, session_id: str, task: CodingTask) -> None:
        session = self.session_mgr.get_session(session_id)
        name = session.ai_profile.name if session else "?"
        self.after(0, lambda: self._status_bar.set_status(
            f"{name}: Working on {task.title}", "info"))

    def _on_session_task_complete(self, session_id: str, task: CodingTask) -> None:
        session = self.session_mgr.get_session(session_id)
        name = session.ai_profile.name if session else "?"
        corner = session.corner if session else ""

        level = "success" if task.status == TaskStatus.COMPLETED else "error"
        msg = f"{name}: {'Completed' if task.status == TaskStatus.COMPLETED else 'Failed'}: {task.title}"
        self.after(0, lambda: self._toast(msg, level))
        self.after(0, lambda: self._status_bar.set_status(msg, level))
        self.after(0, self._refresh_task_list)

        if task.status == TaskStatus.COMPLETED and task.output_code:
            self._last_completed_task = task

        # Auto-save to Downloads
        if task.status == TaskStatus.COMPLETED and task.output_code:
            try:
                path = save_task_output(
                    title=task.title,
                    output=task.output_code,
                    ai_name=name,
                    corner=corner,
                    elapsed_seconds=task.elapsed_seconds,
                    iterations=task.iterations_completed,
                )
                if path:
                    self.after(0, lambda p=path: self._toast(
                        f"Saved to {p.name}", "info"))
            except Exception as e:
                logger.error("Auto-save failed: %s", e)

        # Save to history
        from gemini_coder.history import HistoryEntry
        self._history.add(HistoryEntry(
            entry_type="task",
            title=f"[{name}] {task.title}",
            prompt=task.description,
            response=task.output_code,
            model=name,
            elapsed_seconds=task.elapsed_seconds,
            status=task.status.value,
        ))

    def _on_session_tick(self, session_id: str, task: CodingTask) -> None:
        if session_id == self._active_session_id:
            from datetime import timedelta
            def update():
                elapsed = timedelta(seconds=int(task.elapsed_seconds))
                budget = timedelta(seconds=int(task.time_budget_seconds))
                remaining = max(0, task.time_budget_seconds - task.elapsed_seconds)
                self._task_progress_bar.set(task.progress_fraction)
                self._task_progress_label.configure(
                    text=f"{elapsed} / {budget} ({int(remaining)}s left)")
            self.after(0, update)

    def _on_session_status(self, session_id: str, status: str, detail: str) -> None:
        session = self.session_mgr.get_session(session_id)
        name = session.ai_profile.name if session else "?"
        corner = session.corner if session else ""
        display = f"{name}: {detail}" if detail else f"{name}: {status}"

        # Update the session card's task text
        if corner and corner in self._session_cards:
            card = self._session_cards[corner]
            short = detail[:25] if detail else status
            card._task_text = f"{short}"
            self.after(0, lambda c=card, s=short: c._status_label.configure(text=s))

        c = self._colors
        color_map = {
            "working": c["success"],
            "thinking": c["warning"],
            "improving": "#8e44ad",
            "idle": c["fg_muted"],
            "error": c["error"],
        }
        color = color_map.get(status, c["fg_muted"])

        def update():
            self._ai_status_dot.configure(text_color=color)
            self._ai_status_label.configure(text=display, text_color=color)
        self.after(0, update)

    # ── Task assignment ───────────────────────────────────────────

    def _on_assign_change(self, choice: str) -> None:
        """Change which session receives new tasks."""
        for session in self.session_mgr.sessions:
            label = f"{CORNER_LABELS[session.corner]} ({session.ai_profile.name})"
            if label == choice:
                self._active_session_id = session.session_id
                self._task_queue = session.task_queue
                self._task_executor = session.executor
                if session.client:
                    self._gemini = session.client
                self._refresh_task_list()
                self._toast(f"Tasks now go to {label}", "info")
                return

    def _refresh_all_window_lists(self) -> None:
        """Refresh window picker dropdowns on all session cards."""
        for card in self._session_cards.values():
            card._refresh_window_list()

    def _update_assign_selector(self) -> None:
        """Refresh the session assignment dropdown."""
        values = []
        for session in self.session_mgr.sessions:
            label = f"{CORNER_LABELS[session.corner]} ({session.ai_profile.name})"
            values.append(label)
        if values:
            self._assign_selector.configure(values=values)

    # ── Broadcast mode ─────────────────────────────────────────────

    def _on_broadcast_start(self) -> None:
        task = self._bc_task_input.get("1.0", "end").strip()
        if not task or task.startswith("e.g.,"):
            self._toast("Enter a task description for broadcast", "warning")
            return

        active = [s for s in self.session_mgr.sessions if s.is_configured]
        if not active:
            self._toast("No configured sessions. Launch at least one AI window first.", "error")
            return

        # Auto-start traffic controller if multiple non-CDP sessions
        cdp_sessions = sum(1 for s in active if s.client and s.client.using_cdp)
        pyautogui_sessions = len(active) - cdp_sessions
        if pyautogui_sessions > 1 and TRAFFIC_AVAILABLE:
            if not TrafficClient.is_server_running():
                self._on_start_traffic()
                self._toast("Auto-started Traffic Controller for pyautogui sessions", "info")
        if cdp_sessions > 0:
            self._toast(f"{cdp_sessions} session(s) using CDP (no traffic lock needed)", "info")

        config = BroadcastConfig(
            task=task,
            build_target=self._bc_build_target.get(),
            endless=True,
        )

        self._broadcast.start(config)
        self._bc_start_btn.configure(state="disabled")
        self._bc_stop_btn.configure(state="normal")
        names = ", ".join(s.ai_profile.name for s in active)
        self._toast(f"Broadcasting to {len(active)} sessions: {names}", "success")
        self._status_bar.set_status(f"Broadcast running: {task[:40]}...", "info")

    def _on_broadcast_stop(self) -> None:
        if self._broadcast.is_running:
            self._broadcast.stop()
        self.session_mgr.stop_all()
        self._bc_start_btn.configure(state="normal")
        self._bc_stop_btn.configure(state="disabled")
        self._bc_status.configure(text="Stopped")
        self._toast("Broadcast stopped", "info")

    def _on_broadcast_save(self) -> None:
        """Save all current broadcast outputs to Downloads."""
        saved = 0
        for session in self.session_mgr.sessions:
            sid = session.session_id
            # Use actual AI result, not progress text
            output = self._broadcast._results.get(sid, "")
            if not output or not output.strip():
                output = self._session_outputs.get(sid, "")
            if output and output.strip():
                try:
                    task_text = self._bc_task_input.get("1.0", "end").strip()
                    title = task_text[:60] if task_text and not task_text.startswith("e.g.,") else "broadcast"
                    path = save_task_output(
                        title=title,
                        output=output,
                        ai_name=session.ai_profile.name,
                        corner=session.corner,
                        elapsed_seconds=0,
                        iterations=self._broadcast._iteration_counts.get(sid, 0),
                    )
                    if path:
                        saved += 1
                except Exception as e:
                    logger.error("Save failed for %s: %s", session.display_name, e)
        if saved:
            dl = Path.home() / "Downloads"
            self._toast(f"Saved {saved} files to {dl}", "success")
        else:
            self._toast("No broadcast output to save yet", "warning")

    def _on_broadcast_iteration(self, session_id: str, iteration: int,
                                 focus: str, ai_name: str) -> None:
        # Update the session card with iteration info
        session = self.session_mgr.get_session(session_id)
        if session and session.corner in self._session_cards:
            card = self._session_cards[session.corner]
            card._task_text = f"#{iteration} {focus[:15]}"
            self.after(0, lambda c=card, t=f"#{iteration} {focus[:15]}":
                       c._status_label.configure(text=t))

        def update():
            self._bc_status.configure(
                text=f"{ai_name}: #{iteration} ({focus})"
            )
            self._status_bar.set_status(
                f"Broadcast: {ai_name} iteration #{iteration} - {focus}", "info"
            )
        self.after(0, update)
        # Auto-save is now handled directly by BroadcastController._save_result()

    # ── Override start/stop to work with active session ───────────

    def _on_start_queue(self) -> None:
        if not self._active_session_id:
            self._toast("No session created yet. Set up a session in Settings first.", "error")
            self._show_view("settings")
            return
        session = self.session_mgr.get_session(self._active_session_id)
        if not session:
            self._toast("No active session selected", "error")
            return

        if not session.is_configured:
            self._toast("Launch the AI browser window first in Settings", "error")
            self._show_view("settings")
            return

        if not session.task_queue.pending_tasks:
            self._toast("No pending tasks in queue", "warning")
            return

        self.session_mgr.start_session(self._active_session_id)
        self._start_queue_btn.configure(state="disabled")
        self._stop_queue_btn.configure(state="normal")
        self._kill_resume_btn.configure(state="normal")

    def _on_stop_queue(self) -> None:
        self.session_mgr.stop_session(self._active_session_id)
        self._start_queue_btn.configure(state="normal")
        self._stop_queue_btn.configure(state="disabled")

    def _on_kill_all(self) -> None:
        # Stop broadcast if running
        if self._broadcast.is_running:
            self._broadcast.stop()
            self._bc_start_btn.configure(state="normal")
            self._bc_stop_btn.configure(state="disabled")
            self._bc_status.configure(text="KILLED")

        self.session_mgr.stop_all()
        self._start_queue_btn.configure(state="disabled")
        self._stop_queue_btn.configure(state="disabled")
        self._kill_resume_btn.configure(state="disabled")
        self._resume_btn.configure(state="normal")
        self._status_bar.set_status("KILLED - All sessions stopped", "error")
        self._toast("All sessions killed!", "error")

    def _on_resume_all(self) -> None:
        self._start_queue_btn.configure(state="normal")
        self._stop_queue_btn.configure(state="disabled")
        self._kill_resume_btn.configure(state="disabled")
        self._resume_btn.configure(state="disabled")
        self._status_bar.set_status("Ready - select a session and start", "info")
        self._toast("Resumed", "success")

    # ── CDP browser automation ────────────────────────────────────

    def _on_launch_cdp_browser(self) -> None:
        """Launch dedicated Autocoder Chrome with CDP + all AI chat tabs."""
        # Check if CDP is already running on any port
        active_ports = []
        for port in sorted(set(CDP_CORNER_PORTS.values())):
            if is_cdp_available(port):
                active_ports.append(port)

        if active_ports:
            total_targets = sum(len(discover_cdp_targets(p)) for p in active_ports)
            self._cdp_status.configure(
                text=f"{ICONS['check']} CDP already active! {total_targets} tab(s). Grab them in session cards.",
                text_color=self._colors["success"],
            )
            self._refresh_all_window_lists()
            return

        self._cdp_status.configure(
            text="Launching Autocoder Chrome with AI tabs...",
            text_color=self._colors["warning"],
        )

        def worker():
            import time as _time, json, urllib.request

            ok = launch_chrome_with_cdp(
                url="https://gemini.google.com/app",
            )
            if not ok:
                self.after(0, lambda: self._cdp_status.configure(
                    text="Failed. Close any running Chrome windows first, then try again.",
                    text_color=self._colors["error"],
                ))
                return

            # Open additional AI tabs via CDP
            _time.sleep(2)
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=3)
                data = json.loads(resp.read())
                ws_url = data.get("webSocketDebuggerUrl", "")
                if ws_url:
                    import websocket
                    ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
                    extra_urls = [
                        "https://chatgpt.com",
                        "https://openrouter.ai/chat",
                        "https://claude.ai/new",
                    ]
                    for i, url in enumerate(extra_urls):
                        msg = json.dumps({"id": i + 1, "method": "Target.createTarget", "params": {"url": url}})
                        ws.send(msg)
                        ws.recv()  # Wait for response
                        _time.sleep(0.5)
                    ws.close()
                    _time.sleep(3)
            except Exception as e:
                logger.warning("Could not open extra tabs: %s", e)

            targets = discover_cdp_targets()
            tab_names = ", ".join(t.title[:20] for t in targets if t.tab_type == "page")[:80]
            self.after(0, lambda: self._cdp_status.configure(
                text=f"{ICONS['check']} CDP active! {len(targets)} tab(s): {tab_names}. Log in if needed, then Grab above.",
                text_color=self._colors["success"],
            ))
            self.after(0, lambda: self._toast(
                f"CDP Browser launched with {len(targets)} tabs! Log in to AI sites, then Grab them.", "success"))
            self.after(500, self._refresh_all_window_lists)

        threading.Thread(target=worker, daemon=True).start()

    def _on_check_cdp(self) -> None:
        """Check CDP connectivity on all ports."""
        all_targets = []
        active_ports = []
        for port in sorted(set(CDP_CORNER_PORTS.values())):
            targets = discover_cdp_targets(port)
            if targets:
                active_ports.append(port)
                all_targets.extend(targets)

        if all_targets:
            names = [t.title[:25] for t in all_targets[:6]]
            self._cdp_status.configure(
                text=f"{ICONS['check']} CDP on port(s) {active_ports}: {len(all_targets)} tab(s) — {', '.join(names)}",
                text_color=self._colors["success"],
            )
        else:
            self._cdp_status.configure(
                text="CDP not available. Click 'Launch CDP Browser' first.",
                text_color=self._colors["warning"],
            )

    # ── Traffic controller (same as before) ───────────────────────

    def _on_start_traffic(self) -> None:
        try:
            subprocess.Popen(
                [sys.executable, "-m", "mousetraffic"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            self._traffic_status.configure(
                text=f"{ICONS['check']} Traffic Controller starting...",
                text_color=self._colors["success"],
            )
            self._toast("Traffic Controller started!", "success")
        except Exception as e:
            self._traffic_status.configure(
                text=f"Failed: {e}", text_color=self._colors["error"],
            )

    def _on_check_traffic(self) -> None:
        if TRAFFIC_AVAILABLE:
            status = TrafficClient.get_status()
            if "error" not in status:
                holder = status.get("current_holder_name", "Nobody")
                queue = status.get("queue_depth", 0)
                human = status.get("human_override", False)
                human_txt = " | Human Override!" if human else ""
                self._traffic_status.configure(
                    text=f"{ICONS['check']} Running | Mouse: {holder or 'Free'} | Queue: {queue}{human_txt}",
                    text_color=self._colors["success"],
                )
            else:
                self._traffic_status.configure(
                    text="Not running. Click 'Start Traffic Controller' first.",
                    text_color=self._colors["warning"],
                )
        else:
            self._traffic_status.configure(
                text="mousetraffic package not found",
                text_color=self._colors["error"],
            )

    # ── Overrides for base class ──────────────────────────────────

    def _on_save_api_key(self) -> None:
        pass  # No API keys in browser mode

    def _show_api_key_prompt(self) -> None:
        self._show_view("settings")

    def _on_save_task_settings(self) -> None:
        try:
            default_min = int(self._default_time_input.get().strip())
            if default_min < 1:
                raise ValueError
        except ValueError:
            self._toast("Default minutes must be a positive number", "warning")
            return
        try:
            depth = int(self._depth_input.get().strip())
            if depth < 1:
                raise ValueError
        except ValueError:
            self._toast("Depth limit must be a positive number", "warning")
            return
        self._config_manager.update(
            task_default_minutes=default_min, expand_depth_limit=depth,
        )
        if self._expander:
            self._expander._depth_limit = depth
        self._toast("Settings saved!", "success")

    def _on_close(self) -> None:
        self.session_mgr.stop_all()
        super()._on_close()

    def _build_ui(self) -> None:
        """Build the main UI with tabbed interface."""
        # Create tabview
        self._tabview = ctk.CTkTabview(self, width=250)
        self._tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self._tabview.add("expand")
        self._tabview.add("task queue")
        self._tabview.add("settings")
        self._tabview.set("expand")  # Default tab
        
        # Build each view
        self._build_expand_view()
        self._build_task_queue_view()
        self._build_settings_view()
        
        # Create status bar at bottom
        self._status_bar = StatusBar(self, self._colors)
        self._status_bar.pack(fill="x", side="bottom", padx=5, pady=2)
        
        # Initialize task queue reference
        self._task_queue = TaskQueue()

    def _build_expand_view(self) -> None:
        """Build the prompt expansion view."""
        tab = self._tabview.tab("expand")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Input section
        input_frame = ctk.CTkFrame(tab)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(input_frame, text="Task Description:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        
        self._task_input = ctk.CTkTextbox(input_frame, height=80)
        self._task_input.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self._task_input.insert("1.0", "e.g., Build a calculator app with history")
        
        # Buttons
        btn_frame = ctk.CTkFrame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        self._expand_btn = ctk.CTkButton(
            btn_frame, text="Expand & Send", command=self._on_expand_send
        )
        self._expand_btn.pack(side="left", padx=10, pady=5)
        
        self._clear_btn = ctk.CTkButton(
            btn_frame, text="Clear", command=self._on_clear_input
        )
        self._clear_btn.pack(side="left", padx=10, pady=5)
        
        # Output section
        output_frame = ctk.CTkFrame(tab)
        output_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(output_frame, text="AI Output:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        
        self._task_output = ctk.CTkTextbox(output_frame, wrap="none")
        self._task_output.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Progress bar
        progress_frame = ctk.CTkFrame(output_frame)
        progress_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self._task_progress_bar = ctk.CTkProgressBar(progress_frame)
        self._task_progress_bar.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self._task_progress_bar.set(0)
        
        self._task_progress_label = ctk.CTkLabel(
            progress_frame, text="Ready", font=ctk.CTkFont(size=10)
        )
        self._task_progress_label.grid(row=0, column=1, padx=10, pady=5)

    def _build_task_queue_view(self) -> None:
        """Build the task queue management view."""
        tab = self._tabview.tab("task queue")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Controls
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(control_frame, text="Task Queue", font=ctk.CTkFont(size=16, weight="bold")).pack(
            side="left", padx=10, pady=10
        )
        
        self._add_task_btn = ctk.CTkButton(
            control_frame, text="+ Add Task", command=self._on_add_task
        )
        self._add_task_btn.pack(side="right", padx=10, pady=10)
        
        # Task list
        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self._task_listbox = ctk.CTkTextbox(list_frame, wrap="none")
        self._task_listbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Queue controls
        queue_control_frame = ctk.CTkFrame(tab)
        queue_control_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self._start_queue_btn = ctk.CTkButton(
            queue_control_frame, text="Start Queue", command=self._on_start_queue
        )
        self._start_queue_btn.pack(side="left", padx=5, pady=5)
        
        self._stop_queue_btn = ctk.CTkButton(
            queue_control_frame, text="Stop Queue", command=self._on_stop_queue, state="disabled"
        )
        self._stop_queue_btn.pack(side="left", padx=5, pady=5)
        
        self._kill_resume_btn = ctk.CTkButton(
            queue_control_frame, text="Kill All", command=self._on_kill_all
        )
        self._kill_resume_btn.pack(side="left", padx=5, pady=5)
        
        self._resume_btn = ctk.CTkButton(
            queue_control_frame, text="Resume", command=self._on_resume_all, state="disabled"
        )
        self._resume_btn.pack(side="left", padx=5, pady=5)

    def _on_expand_send(self) -> None:
        """Handle expand and send button click."""
        task_text = self._task_input.get("1.0", "end").strip()
        if not task_text or task_text.startswith("e.g.,"):
            self._toast("Please enter a task description", "warning")
            return
        
        # If bridge is wired, use it to expand and enqueue for the active session
        if getattr(self, "_bridge", None) and getattr(self, "_active_session_id", None):
            try:
                self._bridge.expand_task_for_session(self._active_session_id, task_text)
                self._toast("Expanded and queued", "success")
            except Exception as e:
                self._toast(f"Error: {e}", "error")
            finally:
                self._expand_btn.configure(state="normal", text="Expand & Send")
            return

        # Fallback: legacy path
        
        # Disable button during processing
        self._expand_btn.configure(state="disabled", text="Processing...")
        
        def worker():
            try:
                # Use expander if available
                if self._expander:
                    expanded = self._expander.expand_task(
                        task_text,
                        on_progress=lambda msg: self.after(0, lambda: self._task_progress_label.configure(text=msg))
                    )
                else:
                    expanded = task_text
                
                # Send to active session
                if self._active_session_id:
                    session = self.session_mgr.get_session(self._active_session_id)
                    if session and session.is_configured:
                        # Add to task queue
                        task = CodingTask(
                            title=task_text[:50],
                            description=expanded,
                            session_id=self._active_session_id
                        )
                        session.task_queue.add(task)
                        self.after(0, lambda: self._toast("Task added to queue", "success"))
                    else:
                        self.after(0, lambda: self._toast("Please configure a session first", "error"))
                else:
                    self.after(0, lambda: self._toast("No active session selected", "error"))
            except Exception as e:
                self.after(0, lambda: self._toast(f"Error: {str(e)}", "error"))
            finally:
                self.after(0, lambda: self._expand_btn.configure(state="normal", text="Expand & Send"))
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_clear_input(self) -> None:
        """Clear the input textbox."""
        self._task_input.delete("1.0", "end")

    def _on_add_task(self) -> None:
        """Handle add task button click."""
        task_text = self._task_input.get("1.0", "end").strip()
        if not task_text or task_text.startswith("e.g.,"):
            self._toast("Please enter a task description", "warning")
            return
            
        # Add task to queue
        if self._active_session_id:
            task = CodingTask(
                title=task_text[:50],
                description=task_text,
                session_id=self._active_session_id
            )
            session = self.session_mgr.get_session(self._active_session_id)
            if session:
                session.task_queue.add(task)
                self._toast("Task added to queue", "success")
                self._refresh_task_list()
            else:
                self._toast("No active session", "error")
        else:
            self._toast("Please select a session first", "warning")

    def _refresh_task_list(self) -> None:
        """Refresh the task queue display."""
        if not hasattr(self, '_task_listbox'):
            return
            
        # Get tasks from active session
        tasks = []
        if self._active_session_id:
            session = self.session_mgr.get_session(self._active_session_id)
            if session:
                tasks = session.task_queue.pending_tasks
        
        # Update display
        self._task_listbox.delete("1.0", "end")
        if tasks:
            for i, task in enumerate(tasks, 1):
                self._task_listbox.insert("end", f"{i}. {task.title}\n")
                self._task_listbox.insert("end", f"   {task.description[:100]}...\n\n")
        else:
            self._task_listbox.insert("end", "No tasks in queue")

    def _on_start_queue(self) -> None:
        """Handle start queue button click."""
        if self._active_session_id:
            session = self.session_mgr.get_session(self._active_session_id)
            if session and session.task_queue:
                self.session_mgr.start_session(self._active_session_id)
                self._start_queue_btn.configure(state="disabled")
                self._stop_queue_btn.configure(state="normal")
                self._kill_resume_btn.configure(state="normal")
                self._toast("Queue started", "success")
            else:
                self._toast("No active session or task queue", "error")
        else:
            self._toast("Please select a session first", "warning")

    def _on_stop_queue(self) -> None:
        """Handle stop queue button click."""
        if self._active_session_id:
            self.session_mgr.stop_session(self._active_session_id)
            self._start_queue_btn.configure(state="normal")
            self._stop_queue_btn.configure(state="disabled")
            self._toast("Queue stopped", "info")
        else:
            self._toast("Please select a session first", "warning")
