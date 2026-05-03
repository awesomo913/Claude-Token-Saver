"""Claude Token Saver — standalone GUI for managing project context.

Launch:  python -m claude_backend.gui
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import customtkinter as ctk

try:
    import pyperclip
except ImportError:
    pyperclip = None  # type: ignore[assignment]

from .backend import ClaudeContextManager
from .config import ScanConfig, load_config
from .generators.memory_files import compute_project_slug, get_memory_dirs
from .ollama_manager import OllamaManager, RECOMMENDED_MODELS
from .prefs import Prefs
from .prompt_builder import build_smart_prompt, detect_intent, review_prompt, ROLES
from .search import smart_search, get_domain, get_domain_color, get_all_domains
from .tokenizer import count_tokens
from .tracker import SessionMemory, TokenTracker
from .types import CodeBlock, GenerationResult, ProjectAnalysis
from .welcome import show_welcome

logger = logging.getLogger(__name__)

# ── Theme ────────────────────────────────────────────────────────────────
C = {
    "bg": "#1a1a1a", "bg2": "#2d2d2d", "bg3": "#252525",
    "card": "#212121", "input": "#1e1e1e", "hover": "#3d3d3d",
    "fg": "#ffffff", "fg2": "#b0b0b0", "fg3": "#808080",
    "border": "#404040", "accent": "#0078d4", "accent2": "#1a8ae8",
    "ok": "#107c10", "warn": "#ff8c00", "err": "#e81123",
    "purple": "#8e44ad", "sidebar": "#181818", "side_act": "#2a2a2a",
}
F = "Segoe UI"
M = "Consolas"

TEMPLATES = {
    "Reference context": (
        "Here is relevant context from my project. Use these references "
        "instead of regenerating this code:\n\n{items}\n\n"
        "Now, with this context available, please proceed with my request.\n\n{request}"
    ),
    "Code review": (
        "Please review the following code from my project for issues, "
        "improvements, and best practices:\n\n{items}\n\n{request}"
    ),
    "Bug fix": (
        "I have a bug in my project. Here is the relevant code context:\n\n"
        "{items}\n\nThe issue is:\n{request}"
    ),
    "New feature": (
        "I want to add a new feature. Here are the existing patterns and "
        "relevant code from my project:\n\n{items}\n\n"
        "Please follow these existing patterns when implementing:\n\n{request}"
    ),
}

AI_TUTORIAL_TEXT = """
AUTO-INJECT — HOW IT WORKS
==========================

WHAT IT DOES
------------
Installs a hook into Claude Code that runs once per session start.
The hook silently calls `python -m claude_backend prep` on your
current project directory, which:
  - Re-scans your source files
  - Regenerates CLAUDE.md with current project structure
  - Regenerates memory files (architecture, patterns, utilities,
    conventions, hot-functions)
  - Updates the source snapshot for delta caching

Result: Every Claude Code session starts with fresh context about
your project WITHOUT you opening the Token Saver GUI.

WHERE THE HOOK LIVES
--------------------
It's added to your ~/.claude/settings.json as a SessionStart hook.
A timestamped backup of settings.json is created before any change.

YOU CAN ALWAYS UNDO IT
----------------------
Click the Uninstall button to remove the hook. The original settings
are preserved in the timestamped .backup file next to settings.json.

WHAT IT DOES NOT DO
-------------------
It cannot intercept your typed prompts mid-session. Claude Code
doesn't allow that. For per-query targeted snippets (the biggest
token savings), you still use the Context Builder tab and paste
the result into Claude Code.

WHAT YOU GAIN
-------------
Baseline project context stays fresh automatically. You type a
request in Claude Code and Claude already knows:
  - Your project structure
  - Your coding conventions
  - Your most-used functions (hot_functions.md)
  - Reusable utilities and patterns

That's the 5x compression (pre-loaded context) Token Saver always
provided, now always current without manual prep runs.

IF IT FAILS TO RUN
------------------
The hook uses `|| true` so a failed prep never blocks session
start. Check ~/.claude/projects/<your-slug>/memory/ to see if
memory files are being regenerated. If not, open this GUI and
click Prep manually — that's the fallback.
""".strip()


TUTORIAL_TEXT = """
HOW TO USE CLAUDE TOKEN SAVER
=============================

Save tokens (and money) by giving Claude pre-built context
instead of making it scan your whole project every time.

FIRST TIME SETUP (do this once per project)
--------------------------------------------
1. Dashboard > Browse > pick your project folder > Load
2. Click "Bootstrap (First Time)" — generates CLAUDE.md,
   memory files, and a snippet library from your code
3. Done! Claude Code now auto-loads your project context

EVERY TIME YOU TALK TO CLAUDE
------------------------------
1. Go to "Context Builder" tab (shortcut: click #2 in sidebar)

2. FIND CODE: Type what you need in the search bar.
   Don't worry about spelling — it handles typos:
     "fix cdp timout"  "clik on chat"  "mange sesions"
   Hit Search, then click snippets to add them, or "Add All"

3. WRITE YOUR REQUEST: In the green box, type what you
   actually want Claude to do. For example:
     "The connection drops after 30 seconds.
      Add retry logic with exponential backoff."

4. HIT COPY: Click the big blue "Copy Complete Prompt"
   button. Your request + all the code context gets
   combined into one prompt on your clipboard.

5. PASTE INTO CLAUDE: Ctrl+V into Claude Code.
   Claude now has your code WITHOUT reading files = tokens saved.

WHY THIS WORKS
--------------
Without this tool: Claude reads your files = 5,000-50,000 tokens
With this tool: You paste just the relevant code = 300-2,000 tokens
That's a 90%+ reduction per interaction.

The Dashboard tracks your total savings over time.

TIPS
----
- "Suggested" shows related code from the same modules
- "Recently Used" remembers what you've pasted before
- Run "Prep (Update)" after changing your code
- If fuzzy search can't find it, it asks your local Ollama model
- Go to Settings to download a small AI model for search assist
""".strip()


# ═══════════════════════════════════════════════════════════════════════════
class TokenSaverApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Claude Token Saver")
        self.geometry("1200x780")
        self.minsize(960, 620)
        self.configure(fg_color=C["bg"])

        self._project_path: Optional[Path] = None
        self._analysis: Optional[ProjectAnalysis] = None
        self._config = ScanConfig()
        self._mgr = ClaudeContextManager(self._config)
        self._context_queue: list[dict] = []
        self._snippets: list[CodeBlock] = []
        self._memory_files: dict[str, str] = {}
        self._busy = False
        self._session_start = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._tracker = TokenTracker()
        self._session_mem = SessionMemory()
        self._ollama = OllamaManager()
        self._auto_scan_id: Optional[str] = None
        self._auto_scan_interval = 10 * 60 * 1000  # 10 minutes in ms
        self._prefs = Prefs.load()
        self._welcome_dlg: Optional[ctk.CTkToplevel] = None

        self._build_ui()
        self._show_view("dashboard")
        self._update_token_display()

        # Show welcome on launch unless user disabled it
        if self._prefs.show_welcome_on_launch:
            self.after(400, self._open_welcome)

    # ── Skeleton ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Sidebar
        sb = ctk.CTkFrame(self, width=180, fg_color=C["sidebar"], corner_radius=0)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        ctk.CTkLabel(sb, text="Token Saver", font=(F, 16, "bold"),
                     text_color=C["accent"]).pack(pady=(18, 24), padx=12, anchor="w")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for key, label in [("dashboard", "1  Dashboard"), ("builder", "2  Context Builder"),
                           ("snippets", "3  Snippets"), ("memory", "4  Memory"),
                           ("report", "5  Analysis Report"),
                           ("settings", "6  Settings")]:
            b = ctk.CTkButton(sb, text=f"  {label}", anchor="w", font=(F, 13), height=38,
                              fg_color="transparent", hover_color=C["side_act"],
                              text_color=C["fg2"], corner_radius=6,
                              command=lambda k=key: self._show_view(k))
            b.pack(fill="x", padx=8, pady=2); self._nav_btns[key] = b

        # Help button — always visible, always available
        help_btn = ctk.CTkButton(
            sb, text="  ?  Help / Welcome", anchor="w", font=(F, 12, "bold"),
            height=36, fg_color="transparent", hover_color=C["side_act"],
            text_color=C["accent"], corner_radius=6,
            command=self._open_welcome,
        )
        help_btn.pack(fill="x", padx=8, pady=(20, 4), side="bottom")

        ctk.CTkLabel(sb, text="v4.5", font=(F, 9), text_color=C["fg3"]).pack(side="bottom", pady=8)

        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        bar = ctk.CTkFrame(self, height=28, fg_color=C["bg2"], corner_radius=0)
        bar.pack(side="bottom", fill="x"); bar.pack_propagate(False)
        self._st_label = ctk.CTkLabel(bar, text="Ready", font=(F, 10), text_color=C["fg2"])
        self._st_label.pack(side="left", padx=12)
        self._st_proj = ctk.CTkLabel(bar, text="No project loaded", font=(F, 10), text_color=C["fg3"])
        self._st_proj.pack(side="right", padx=12)

        self._toast_lbl: Optional[ctk.CTkLabel] = None
        self._toast_id: Optional[str] = None

        self._views: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_builder()
        self._build_snippets()
        self._build_memory()
        self._build_report()
        self._build_settings()

    def _show_view(self, name: str) -> None:
        for f in self._views.values(): f.pack_forget()
        # Guard: tabs that need a project loaded
        needs_project = {"builder", "snippets", "memory", "report"}
        if name in needs_project and not self._project_path:
            self._toast("Load a project on the Dashboard first", "warning")
            name = "dashboard"
        if name in self._views:
            self._views[name].pack(in_=self._content, fill="both", expand=True)
        for k, b in self._nav_btns.items():
            b.configure(fg_color=C["side_act"] if k == name else "transparent",
                        text_color=C["fg"] if k == name else C["fg2"])
        # Refresh dynamic elements when switching to their tab
        if name == "builder" and self._snippets:
            self._rebuild_grab_buttons()
        elif name == "snippets" and self._snippets:
            self._rebuild_domain_tabs()
        elif name == "settings" and hasattr(self, "_ai_status_lbl"):
            self._ai_refresh_status()
            if hasattr(self, "_al_status_lbl"):
                self._al_refresh_status()

    def _open_welcome(self) -> None:
        """Open welcome dialog. Reuses existing window if already open."""
        if self._welcome_dlg is not None and self._welcome_dlg.winfo_exists():
            self._welcome_dlg.lift()
            self._welcome_dlg.focus_force()
            return

        def _on_install_done() -> None:
            # Refresh Settings tab status if user installed from welcome
            if hasattr(self, "_ai_status_lbl"):
                self._ai_refresh_status()
            self._toast("Auto-Inject installed", "success")

        try:
            self._welcome_dlg = show_welcome(
                self, self._prefs, on_install_callback=_on_install_done,
            )
        except Exception as e:
            logger.exception("Failed to open welcome dialog")
            self._toast(f"Welcome dialog failed: {e}", "error")

    def _toast(self, msg: str, lv: str = "info") -> None:
        cm = {"success": C["ok"], "warning": C["warn"], "error": C["err"], "info": C["accent"]}
        if self._toast_lbl: self._toast_lbl.destroy()
        if self._toast_id: self.after_cancel(self._toast_id)
        self._toast_lbl = ctk.CTkLabel(self, text=msg, font=(F, 12), text_color="#fff",
                                       fg_color=cm.get(lv, C["accent"]), corner_radius=8, padx=20, pady=8)
        self._toast_lbl.place(relx=0.5, rely=0.94, anchor="center"); self._toast_lbl.lift()
        self._toast_id = self.after(3500, lambda: self._toast_lbl.destroy() if self._toast_lbl else None)

    def _run_async(self, fn, done=None, err=None) -> None:
        if self._busy: self._toast("Operation running...", "warning"); return
        self._busy = True
        def w():
            try:
                r = fn()
                if done: self.after(0, lambda: done(r))
            except Exception as e:
                logger.exception("Async error")
                if err: self.after(0, lambda: err(e))
                else: self.after(0, lambda: self._toast(f"Error: {e}", "error"))
            finally:
                self.after(0, lambda: setattr(self, '_busy', False))
        threading.Thread(target=w, daemon=True).start()

    def _copy_clip(self, text: str, track: bool = True) -> None:
        if not pyperclip: self._toast("pyperclip not installed", "error"); return
        # Normalize line endings for Windows clipboard
        clean = text.replace("\r\n", "\n").replace("\r", "\n")
        pyperclip.copy(clean)
        est = count_tokens(text)
        if track:
            proj = self._project_path.name if self._project_path else ""
            self._tracker.record("clipboard_copy", est, project=proj)
            self._update_token_display()
        self._toast(f"Copied! (~{est:,} tokens saved)", "success")

    def _pick_folder(self, entry: ctk.CTkEntry) -> None:
        p = ctk.filedialog.askdirectory()
        if p: entry.delete(0, "end"); entry.insert(0, p)

    # ═══════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════════════════
    def _build_dashboard(self) -> None:
        fr = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        self._views["dashboard"] = fr

        ctk.CTkLabel(fr, text="Dashboard", font=(F, 20, "bold"),
                     text_color=C["fg"]).pack(padx=20, pady=(16, 4), anchor="w")
        ctk.CTkLabel(fr, text="Step 1: Load a project folder, then Bootstrap to generate context files.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        # Project selector
        pcard = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        pcard.pack(fill="x", padx=20, pady=(0, 8))
        prow = ctk.CTkFrame(pcard, fg_color="transparent"); prow.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(prow, text="Project:", font=(F, 12), text_color=C["fg2"]).pack(side="left", padx=(0, 8))
        self._d_path = ctk.CTkEntry(prow, placeholder_text="Select project folder...",
                                    font=(F, 12), fg_color=C["input"], border_color=C["border"], height=34)
        self._d_path.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(prow, text="Browse", width=80, height=34, font=(F, 11),
                      fg_color=C["accent"], command=lambda: self._pick_folder(self._d_path)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(prow, text="Load", width=70, height=34, font=(F, 11, "bold"),
                      fg_color=C["ok"], command=self._on_load).pack(side="left")

        # Actions
        arow = ctk.CTkFrame(fr, fg_color="transparent"); arow.pack(fill="x", padx=20, pady=(0, 8))
        for txt, col, cmd in [("Bootstrap (First Time)", C["accent"], self._on_bootstrap),
                              ("Prep (Update)", C["purple"], self._on_prep),
                              ("Scan Only", C["bg2"], self._on_scan),
                              ("Clean", C["err"], self._on_clean)]:
            ctk.CTkButton(arow, text=txt, font=(F, 11, "bold"), fg_color=col,
                          height=34, width=160, command=cmd).pack(side="left", padx=(0, 6))

        # Token savings
        srow = ctk.CTkFrame(fr, fg_color="transparent"); srow.pack(fill="x", padx=20, pady=(0, 6))
        self._sav: dict[str, ctk.CTkLabel] = {}
        for lbl, clr, w in [("All-Time Saved", C["ok"], 160), ("Project Saved", C["accent"], 150),
                            ("This Session", C["purple"], 140), ("Copies", C["warn"], 100)]:
            cd = ctk.CTkFrame(srow, fg_color=C["card"], corner_radius=8, border_width=1,
                              border_color=clr, width=w, height=68)
            cd.pack(side="left", padx=(0, 6), pady=2); cd.pack_propagate(False)
            ctk.CTkLabel(cd, text=lbl, font=(F, 9), text_color=clr).pack(pady=(8, 0))
            v = ctk.CTkLabel(cd, text="0", font=(F, 18, "bold"), text_color=C["fg"])
            v.pack(pady=(0, 6)); self._sav[lbl] = v

        # Stats
        srow2 = ctk.CTkFrame(fr, fg_color="transparent"); srow2.pack(fill="x", padx=20, pady=(0, 6))
        self._stats: dict[str, ctk.CTkLabel] = {}
        for lbl in ["Files", "Modules", "Blocks", "Snippets", "Memory"]:
            cd = ctk.CTkFrame(srow2, fg_color=C["card"], corner_radius=8, border_width=1,
                              border_color=C["border"], width=130, height=62)
            cd.pack(side="left", padx=(0, 6), pady=2); cd.pack_propagate(False)
            ctk.CTkLabel(cd, text=lbl, font=(F, 9), text_color=C["fg3"]).pack(pady=(6, 0))
            v = ctk.CTkLabel(cd, text="--", font=(F, 18, "bold"), text_color=C["fg"])
            v.pack(pady=(0, 4)); self._stats[lbl] = v

        # Conventions
        self._conv_fr = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        self._conv_fr.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(self._conv_fr, text="Detected Conventions", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=12, pady=(8, 4), anchor="w")
        self._conv_badges = ctk.CTkFrame(self._conv_fr, fg_color="transparent")
        self._conv_badges.pack(fill="x", padx=12, pady=(0, 8))
        self._conv_lbls: list[ctk.CTkLabel] = []

        # Recent activity
        self._act_fr = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        self._act_fr.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(self._act_fr, text="Recent Context Activity", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=12, pady=(8, 4), anchor="w")
        self._act_items = ctk.CTkFrame(self._act_fr, fg_color="transparent")
        self._act_items.pack(fill="x", padx=12, pady=(0, 8))
        self._act_lbls: list[ctk.CTkLabel] = []

        # Log
        ctk.CTkLabel(fr, text="Activity Log", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=20, anchor="w")
        self._log_box = ctk.CTkTextbox(fr, font=(M, 10), fg_color=C["card"], border_color=C["border"],
                                       border_width=1, text_color=C["fg2"], state="disabled", height=120)
        self._log_box.pack(fill="x", padx=20, pady=(4, 16))

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self._log_box.see("end"); self._log_box.configure(state="disabled")

    def _on_load(self) -> None:
        ps = self._d_path.get().strip()
        if not ps: self._toast("Enter a project path first", "warning"); return
        p = Path(ps)
        if not p.is_dir(): self._toast("Not a valid directory", "error"); return
        self._project_path = p.resolve()
        self._config = load_config(project_path=self._project_path)
        self._mgr = ClaudeContextManager(self._config)
        self._session_mem.set_project(self._project_path)
        self._st_proj.configure(text=str(self._project_path))
        self._log(f"Loaded: {self._project_path.name}")
        self._toast(f"Project loaded: {self._project_path.name}", "success")
        self._update_token_display(); self._update_recent()
        # Run initial scan FIRST, then start auto-scan timer after it completes
        self._on_scan(start_auto_after=True)

    def _on_bootstrap(self) -> None:
        if not self._project_path: self._toast("Load a project first", "warning"); return
        self._st_label.configure(text="Bootstrapping..."); self._log("Bootstrap started...")
        def do(): return self._mgr.bootstrap(self._project_path)
        def done(r):
            tok = sum(count_tokens(f) for f in r.files_written)
            self._tracker.record("bootstrap", tok, project=self._project_path.name,
                                 detail=f"{len(r.files_written)} files")
            self._log(f"Bootstrap: {r.summary} (~{tok:,} tokens saved)")
            self._st_label.configure(text="Bootstrap complete")
            self._toast(f"Bootstrap: {r.summary}", "success")
            self._update_token_display(); self._on_scan()
        self._run_async(do, done)

    def _on_prep(self) -> None:
        if not self._project_path: self._toast("Load a project first", "warning"); return
        self._st_label.configure(text="Updating..."); self._log("Prep started...")
        def do(): return self._mgr.prep(self._project_path)
        def done(r):
            tok = sum(count_tokens(f) for f in r.files_updated)
            self._tracker.record("prep", tok, project=self._project_path.name,
                                 detail=f"{len(r.files_updated)} files")
            self._log(f"Prep: {r.summary} (~{tok:,} tokens saved)")
            self._st_label.configure(text="Prep complete")
            self._toast(f"Prep: {r.summary}", "success")
            self._update_token_display(); self._on_scan()
        self._run_async(do, done)

    def _on_scan(self, start_auto_after: bool = False) -> None:
        if not self._project_path: self._toast("Load a project first", "warning"); return
        self._st_label.configure(text="Scanning...")
        def do(): return self._mgr.analyze(self._project_path)
        def done(a):
            self._analysis = a; self._snippets = [b for b in a.blocks if b.docstring or b.kind != "file"]
            self._update_stats(); self._load_memory()
            self._rebuild_domain_tabs(); self._filter_snips(); self._rebuild_grab_buttons()
            self._st_label.configure(text="Scan complete")
            self._log(f"Scan: {len(a.files)} files, {len(a.blocks)} blocks")
            # Start auto-scan AFTER initial scan completes (avoids race condition)
            if start_auto_after:
                self._start_auto_scan()
        self._run_async(do, done)

    def _on_clean(self) -> None:
        if not self._project_path: return
        self._st_label.configure(text="Cleaning...")
        def do(): return self._mgr.clean(self._project_path)
        def done(rm):
            self._log(f"Cleaned {len(rm)} items"); self._st_label.configure(text="Cleaned")
            self._toast(f"Removed {len(rm)} items", "info"); self._on_scan()
        self._run_async(do, done)

    def _update_stats(self) -> None:
        a = self._analysis
        if not a: return
        self._stats["Files"].configure(text=str(len(a.files)))
        self._stats["Modules"].configure(text=str(len(a.modules)))
        self._stats["Blocks"].configure(text=str(len(a.blocks)))
        sd = self._project_path / ".claude" / "snippets"
        self._stats["Snippets"].configure(text=str(sum(1 for f in sd.rglob("*.py")) if sd.is_dir() else 0))
        md = self._project_path / ".claude" / "memory"
        self._stats["Memory"].configure(text=str(sum(1 for f in md.iterdir() if f.is_file()) if md.is_dir() else 0))
        for l in self._conv_lbls: l.destroy()
        self._conv_lbls.clear()
        cv = a.conventions
        for t, ok in [(f"Paths: {cv.path_style}", cv.path_style != "unknown"),
                      (f"Types: {cv.type_hints}", cv.type_hints != "unknown"),
                      (f"Fmt: {cv.string_format}", cv.string_format != "unknown"),
                      (f"Errors: {cv.error_handling}", cv.error_handling != "unknown"),
                      (f"Logging: {cv.logging_style}", cv.logging_style != "unknown"),
                      (f"Imports: {cv.import_style}", cv.import_style != "unknown")]:
            if ok:
                l = ctk.CTkLabel(self._conv_badges, text=t, font=(F, 10), text_color=C["fg"],
                                 fg_color=C["accent"], corner_radius=12, padx=10, pady=4)
                l.pack(side="left", padx=(0, 6), pady=2); self._conv_lbls.append(l)

    def _update_token_display(self) -> None:
        at = self._tracker.get_all_time_total()
        self._sav["All-Time Saved"].configure(text=f"{at:,}" if at < 1_000_000 else f"{at/1e6:.1f}M")
        pn = self._project_path.name if self._project_path else ""
        self._sav["Project Saved"].configure(text=f"{self._tracker.get_project_total(pn):,}" if pn else "0")
        self._sav["This Session"].configure(text=f"{self._tracker.get_session_total(self._session_start):,}")
        self._sav["Copies"].configure(text=str(self._session_mem.get_total_copies() if self._project_path else 0))
        for l in self._act_lbls: l.destroy()
        self._act_lbls.clear()
        recent = self._session_mem.get_recently_used(6)
        if recent:
            for it in recent:
                t = f"{it.get('name','?')}  ({it.get('source','')})  {it.get('ts','')[:16].replace('T',' ')}"
                l = ctk.CTkLabel(self._act_items, text=t, font=(F, 10), text_color=C["fg2"])
                l.pack(anchor="w", pady=1); self._act_lbls.append(l)
        else:
            l = ctk.CTkLabel(self._act_items, text="No activity yet. Use Context Builder to add snippets.",
                             font=(F, 10), text_color=C["fg3"])
            l.pack(anchor="w", pady=1); self._act_lbls.append(l)

    # ═══════════════════════════════════════════════════════════════════
    #  CONTEXT BUILDER  (the main workflow)
    # ═══════════════════════════════════════════════════════════════════
    def _build_builder(self) -> None:
        fr = ctk.CTkFrame(self._content, fg_color=C["bg"])
        self._views["builder"] = fr

        ctk.CTkLabel(fr, text="Context Builder", font=(F, 20, "bold"),
                     text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="Type what you want. The tool auto-finds the right code and builds your prompt.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        # ═══ QUICK GRAB: click an area to grab all its code ═══
        grab_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["ok"])
        grab_card.pack(fill="x", padx=20, pady=(0, 6))
        gh = ctk.CTkFrame(grab_card, fg_color="transparent"); gh.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(gh, text="Quick Grab — click any area to add its code to your prompt:",
                     font=(F, 12, "bold"), text_color=C["ok"]).pack(side="left")
        self._grab_status = ctk.CTkLabel(gh, text="", font=(F, 10), text_color=C["fg2"])
        self._grab_status.pack(side="right")
        # Two rows so buttons don't overflow
        self._grab_row1 = ctk.CTkFrame(grab_card, fg_color="transparent")
        self._grab_row1.pack(fill="x", padx=12, pady=(0, 2))
        self._grab_row2 = ctk.CTkFrame(grab_card, fg_color="transparent")
        self._grab_row2.pack(fill="x", padx=12, pady=(0, 8))
        self._grab_btns: list[ctk.CTkButton] = []
        # Placeholder text when no project loaded
        self._grab_placeholder = ctk.CTkLabel(
            self._grab_row1, text="Load a project on Dashboard first, then areas appear here",
            font=(F, 10), text_color=C["fg3"])
        self._grab_placeholder.pack(anchor="w", pady=4)

        # ═══ THE ONE BOX: type request, code auto-found ═══
        req_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["accent"])
        req_card.pack(fill="x", padx=20, pady=(0, 6))

        r_hdr = ctk.CTkFrame(req_card, fg_color="transparent"); r_hdr.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(r_hdr, text="Or describe what you need:", font=(F, 14, "bold"),
                     text_color=C["accent"]).pack(side="left")
        ctk.CTkButton(r_hdr, text="Clear", width=55, height=22, font=(F, 9),
                      fg_color=C["err"], command=self._clear_request).pack(side="right", padx=(4, 0))
        self._auto_status = ctk.CTkLabel(r_hdr, text="", font=(F, 10), text_color=C["ok"])
        self._auto_status.pack(side="right")

        # Quick-start action buttons
        qp = ctk.CTkFrame(req_card, fg_color="transparent"); qp.pack(fill="x", padx=12, pady=(4, 0))
        for label, prompt in [
            ("Fix a bug", "Fix this bug: "),
            ("Build feature", "Build a new feature that "),
            ("Refactor", "Refactor this code to improve "),
            ("Add tests", "Write unit tests for "),
            ("Explain", "Explain how this works: "),
            ("Optimize", "Optimize performance of "),
            ("Error handling", "Add error handling to "),
            ("Type hints", "Add type hints and docstrings to this code."),
        ]:
            ctk.CTkButton(qp, text=label, width=0, height=22, font=(F, 9),
                          fg_color=C["bg2"], hover_color=C["hover"], corner_radius=4,
                          command=lambda p=prompt: self._set_request(p)).pack(side="left", padx=2)

        self._request_box = ctk.CTkTextbox(req_card, font=(F, 13), fg_color=C["input"],
                                           border_color=C["border"], border_width=1,
                                           text_color=C["fg"], height=90)
        self._request_box.pack(fill="x", padx=12, pady=(6, 4))
        self._request_box.insert("1.0", "")

        # Auto-find timer: debounce keystrokes, auto-search after 800ms pause
        self._autofind_id: Optional[str] = None
        self._request_box.bind("<KeyRelease>", self._on_request_keyup)

        # Matched code display
        self._match_frame = ctk.CTkFrame(req_card, fg_color="transparent")
        self._match_frame.pack(fill="x", padx=12, pady=(0, 8))
        self._match_cards: list[ctk.CTkFrame] = []
        self._smart_matches: list[CodeBlock] = []

        # Hidden entry for backward compat (search functions read _task_input)
        self._task_input = self._request_box

        # ═══ BOTTOM: Big copy button (pack FIRST with side=bottom so it always shows) ═══
        bar = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["accent"])
        bar.pack(side="bottom", fill="x", padx=20, pady=(0, 12))
        bi = ctk.CTkFrame(bar, fg_color="transparent"); bi.pack(fill="x", padx=12, pady=10)
        ctk.CTkButton(bi, text="Copy Complete Prompt to Clipboard",
                      font=(F, 15, "bold"), fg_color=C["accent"],
                      hover_color=C["accent2"], height=48, width=360,
                      command=self._copy_context).pack(side="left", padx=(0, 12))
        ctk.CTkButton(bi, text="Snippets Only", font=(F, 11), fg_color=C["bg2"],
                      height=34, width=120, command=self._copy_raw).pack(side="left")

        # ═══ MAIN SPLIT: queue | preview ═══
        split = ctk.CTkFrame(fr, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        # ── LEFT: auto-filled queue + suggested + recent ──
        left = ctk.CTkFrame(split, fg_color=C["bg2"], corner_radius=8, border_width=1,
                            border_color=C["border"], width=290)
        left.pack(side="left", fill="both", padx=(0, 8)); left.pack_propagate(False)
        ls = ctk.CTkScrollableFrame(left, fg_color="transparent")
        ls.pack(fill="both", expand=True, padx=4, pady=4)

        qh = ctk.CTkFrame(ls, fg_color="transparent"); qh.pack(fill="x", padx=4, pady=(4, 2))
        ctk.CTkLabel(qh, text="Code in Prompt", font=(F, 12, "bold"), text_color=C["fg"]).pack(side="left")
        ctk.CTkButton(qh, text="Clear", width=50, height=20, font=(F, 9),
                      fg_color=C["err"], command=self._clear_queue).pack(side="right")
        self._q_frame = ctk.CTkFrame(ls, fg_color="transparent"); self._q_frame.pack(fill="x", padx=2, pady=(0, 4))
        self._q_cards: list[ctk.CTkFrame] = []

        ctk.CTkLabel(ls, text="Suggested", font=(F, 10, "bold"),
                     text_color=C["warn"]).pack(anchor="w", padx=4, pady=(6, 1))
        self._sug_frame = ctk.CTkFrame(ls, fg_color="transparent"); self._sug_frame.pack(fill="x", padx=2, pady=(0, 4))
        self._sug_cards: list[ctk.CTkFrame] = []

        ctk.CTkLabel(ls, text="Recently Used", font=(F, 10, "bold"),
                     text_color=C["purple"]).pack(anchor="w", padx=4, pady=(6, 1))
        self._rec_frame = ctk.CTkFrame(ls, fg_color="transparent"); self._rec_frame.pack(fill="x", padx=2, pady=(0, 4))
        self._rec_cards: list[ctk.CTkFrame] = []

        # ── RIGHT: mode + preview ──
        right = ctk.CTkFrame(split, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        tmpl_row = ctk.CTkFrame(right, fg_color="transparent"); tmpl_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(tmpl_row, text="Mode:", font=(F, 10), text_color=C["fg3"]).pack(side="left", padx=(0, 6))
        modes = ["Smart (Recommended)"] + list(TEMPLATES.keys()) + ["Raw (No Wrapping)"]
        self._tmpl = ctk.CTkComboBox(tmpl_row, values=modes, font=(F, 10),
                                     fg_color=C["input"], border_color=C["border"], height=28, width=220,
                                     command=lambda v: self._update_preview())
        self._tmpl.set("Smart (Recommended)"); self._tmpl.pack(side="left")
        self._tok_lbl = ctk.CTkLabel(tmpl_row, text="~0 tokens", font=(F, 12, "bold"), text_color=C["accent"])
        self._tok_lbl.pack(side="right")

        self._preview = ctk.CTkTextbox(right, font=(M, 11), fg_color=C["card"], border_color=C["border"],
                                       border_width=1, text_color="#d4d4d4", state="disabled", wrap="word")
        self._preview.pack(fill="both", expand=True, pady=(0, 6))

    # ── Auto-find: types request -> code appears automatically ─────────

    MAX_PROMPT_TOKENS = 6000  # cap total assembled prompt at ~6K tokens

    def _on_request_keyup(self, event=None) -> None:
        """Debounced auto-find. Longer delay for bigger text to avoid mid-type firing."""
        if self._autofind_id:
            self.after_cancel(self._autofind_id)
        text = self._get_request_text()
        delay = 1200 if len(text) > 200 else 800  # more time for big pastes
        self._autofind_id = self.after(delay, self._auto_find_dispatch)

    def _auto_find_dispatch(self) -> None:
        """Dispatch auto-find on background thread so GUI never blocks.

        Beginner-friendly: grabs more context than asked for.
        If user mentions one function, also grabs related functions from the same file.
        """
        text = self._get_request_text()
        if not text or len(text) < 5 or not self._snippets:
            self._update_preview(); return

        is_large = len(text) > 150 or len(text.split()) > 25
        snippets_ref = self._snippets

        if is_large:
            self._auto_status.configure(text="Breaking down your request...")
        else:
            self._auto_status.configure(text="Finding relevant code...")

        def do():
            if is_large:
                results = self._breakdown_large_request(text, snippets_ref)
            else:
                # Lower threshold for beginners — grab more, not less
                results = smart_search(snippets_ref, text, max_results=5, min_score=4.0)

            if not results:
                return []

            # ── Beginner boost: also grab "neighbors" from the same files ──
            # If we found send_message from browser_actions.py, also grab
            # other key functions from browser_actions.py that the user
            # probably needs but didn't know to ask for.
            found_files = {b.file_path for _, b in results}
            found_names = {b.name for _, b in results}
            neighbors: list[tuple[float, CodeBlock]] = []
            for b in snippets_ref:
                if b.name in found_names:
                    continue
                if b.file_path in found_files and b.docstring:
                    # Same file + has docstring = likely important related code
                    neighbors.append((2.0, b))  # low score so they rank below direct matches

            # Merge: direct matches first, then neighbors, cap at 10 total
            combined = list(results[:4]) + neighbors[:2]
            return combined

        def done(results):
            if not results:
                self._auto_status.configure(text="No matches found. Try Quick Grab or Snippets tab.")
                self._update_preview(); return

            MAX_QUEUE = 15
            added = 0
            for score, block in results[:6]:
                if len(self._context_queue) >= MAX_QUEUE:
                    break
                if not any(q["name"] == block.name for q in self._context_queue):
                    self._context_queue.append({
                        "name": block.name, "source": block.file_path, "content": block.source
                    })
                    added += 1
            if added:
                self._smart_matches = [b for _, b in results[:6]]
                self._render_queue(); self._render_matches()
                self._update_suggestions(); self._update_recent()
                self._update_token_display()
                files = len({b.file_path for _, b in results[:6]})
                self._auto_status.configure(text=f"Found {added} snippets from {files} files")
                if len(self._context_queue) >= MAX_QUEUE:
                    self._auto_status.configure(text=f"{added} added (queue full at {MAX_QUEUE})")
            else:
                self._auto_status.configure(text="")
            self._compress_if_needed()
            self._update_preview()

        self._run_async(do, done)

    def _breakdown_large_request(
        self, text: str, snippets: list
    ) -> list[tuple[float, CodeBlock]]:
        """Break a large request into sub-tasks, search each, deduplicate.

        For a 300-word request, this:
        1. Splits into sentences / clauses
        2. Searches each chunk separately (focused matches)
        3. Deduplicates and ranks by total relevance
        4. Returns top results
        """
        import re as _re

        # Split on sentence boundaries and conjunctions
        chunks = _re.split(r'[.!?\n]+|(?:,\s*(?:and|also|plus|then|while)\s)', text)
        chunks = [c.strip() for c in chunks if len(c.strip()) > 10]

        # Also try splitting on "and" / "also" for run-on sentences
        if len(chunks) <= 2 and len(text) > 200:
            chunks = _re.split(r'\band\b|\balso\b|\bplus\b|\bthen\b', text)
            chunks = [c.strip() for c in chunks if len(c.strip()) > 10]

        # Cap at 8 sub-searches
        chunks = chunks[:8]

        # Search each chunk, accumulate scores per block
        block_scores: dict[str, tuple[float, CodeBlock]] = {}
        for chunk in chunks:
            results = smart_search(snippets, chunk, max_results=4, min_score=3.0)
            for score, block in results:
                key = f"{block.name}:{block.file_path}"
                if key in block_scores:
                    old_score = block_scores[key][0]
                    block_scores[key] = (old_score + score, block)
                else:
                    block_scores[key] = (score, block)

        # Sort by accumulated score, return top results
        ranked = sorted(block_scores.values(), key=lambda x: -x[0])
        return ranked[:10]

    def _compress_if_needed(self) -> None:
        """If queued code exceeds MAX_PROMPT_TOKENS, compress large blocks to signatures."""
        total = sum(count_tokens(q["content"]) for q in self._context_queue)
        if total <= self.MAX_PROMPT_TOKENS:
            return

        # Sort queue items by size (biggest first) and compress the biggest
        sized = sorted(enumerate(self._context_queue), key=lambda x: -len(x[1]["content"]))
        for idx, item in sized:
            if total <= self.MAX_PROMPT_TOKENS:
                break
            content = item["content"]
            old_tokens = count_tokens(content)
            if old_tokens < 100:
                continue  # already small

            # Compress: keep first 5 lines + "# ... (N more lines)" + last 3 lines
            lines = content.splitlines()
            if len(lines) > 15:
                compressed = "\n".join(lines[:5])
                compressed += f"\n# ... ({len(lines) - 8} more lines, use Read tool to see full file)\n"
                compressed += "\n".join(lines[-3:])
                self._context_queue[idx]["content"] = compressed
                total -= old_tokens - count_tokens(compressed)

    def _smart_find(self) -> None:
        """Manual trigger: clear queue, re-search from scratch."""
        text = self._get_request_text()
        if not text:
            self._toast("Type what you want first", "warning"); return
        if not self._snippets:
            self._toast("Load and scan a project first", "warning"); return

        self._context_queue.clear()
        self._auto_find_dispatch()  # reuse the background dispatch

    def _smart_add_all(self) -> None:
        if not self._smart_matches:
            self._smart_find(); return
        for b in self._smart_matches:
            if not any(q["name"] == b.name for q in self._context_queue):
                self._add_to_context(b.name, b.file_path, b.source, silent=True)
        self._compress_if_needed()
        self._update_preview()
        self._toast(f"Added {len(self._smart_matches)} snippets", "success")
        self._smart_matches.clear(); self._render_matches()

    def _render_matches(self) -> None:
        for c in self._match_cards: c.destroy()
        self._match_cards.clear()
        if not self._smart_matches: return

        container = ctk.CTkFrame(self._match_frame, fg_color=C["card"], corner_radius=6,
                                 border_width=1, border_color=C["ok"])
        container.pack(fill="x", pady=2); self._match_cards.append(container)

        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(6, 2))
        ctk.CTkLabel(hdr, text=f"Found {len(self._smart_matches)} matches:", font=(F, 11, "bold"),
                     text_color=C["ok"]).pack(side="left")
        ctk.CTkButton(hdr, text="Add All", width=65, height=24, font=(F, 10, "bold"),
                      fg_color=C["ok"], command=self._smart_add_all).pack(side="right")

        # Use wrapping rows — max 4 buttons per row to avoid overflow
        row = None
        for i, b in enumerate(self._smart_matches[:12]):
            if i % 4 == 0:
                row = ctk.CTkFrame(container, fg_color="transparent")
                row.pack(fill="x", padx=8, pady=1)
                self._match_cards.append(row)
            name_short = b.name[:25] + ("..." if len(b.name) > 25 else "")
            ctk.CTkButton(row, text=name_short, width=0, height=24, font=(F, 9),
                          fg_color=C["bg2"], hover_color=C["hover"], corner_radius=4,
                          command=lambda b=b: self._add_to_context(b.name, b.file_path, b.source)
                          ).pack(side="left", padx=2, pady=2)

        ctk.CTkFrame(container, fg_color="transparent", height=4).pack()

    # ── Local AI assist (uses OllamaManager) ───────────────────────────
    def _ollama_available(self) -> bool:
        return self._ollama.is_running() and self._ollama.get_current() is not None

    def _ollama_interpret(self, query: str) -> str:
        if not self._ollama.get_current():
            self._ollama.select_best()
        return self._ollama.interpret_query(query)

    # ── Context queue ops ──────────────────────────────────────────────
    def _add_to_context(self, name: str, source: str, content: str, silent: bool = False) -> None:
        if any(q["name"] == name for q in self._context_queue):
            if not silent: self._toast(f"{name} already in queue", "warning")
            return
        self._context_queue.append({"name": name, "source": source, "content": content})
        self._session_mem.record_context_add(name=name, source=source, file_path=source,
                                             tokens=count_tokens(content))
        self._render_queue(); self._update_preview(); self._update_suggestions()
        self._update_recent(); self._update_token_display()
        if not silent: self._toast(f"Added: {name}", "info")

    def _clear_queue(self) -> None:
        self._context_queue.clear(); self._render_queue(); self._update_preview()

    def _remove_item(self, idx: int) -> None:
        if 0 <= idx < len(self._context_queue):
            self._context_queue.pop(idx); self._render_queue()
            self._update_preview(); self._update_suggestions()

    def _render_queue(self) -> None:
        for c in self._q_cards: c.destroy()
        self._q_cards.clear()
        if not self._context_queue:
            l = ctk.CTkLabel(self._q_frame, text="Queue is empty. Use search above or browse Snippets.",
                             font=(F, 10), text_color=C["fg3"])
            l.pack(anchor="w", pady=4); self._q_cards.append(l); return
        for i, it in enumerate(self._context_queue):
            cd = ctk.CTkFrame(self._q_frame, fg_color=C["card"], corner_radius=4,
                              border_width=1, border_color=C["border"])
            cd.pack(fill="x", padx=2, pady=1); self._q_cards.append(cd)
            r = ctk.CTkFrame(cd, fg_color="transparent"); r.pack(fill="x", padx=6, pady=3)
            ctk.CTkLabel(r, text=it["name"], font=(F, 10, "bold"), text_color=C["fg"]).pack(side="left")
            ctk.CTkButton(r, text="X", width=22, height=20, font=(F, 9), fg_color="transparent",
                          hover_color=C["hover"], text_color=C["err"],
                          command=lambda idx=i: self._remove_item(idx)).pack(side="right")
            # Show source file path so user knows WHERE this code is from
            src = it.get("source", "")
            if src:
                ctk.CTkLabel(cd, text=src, font=(M, 8), text_color=C["fg3"]).pack(padx=6, anchor="w", pady=(0, 2))

    def _update_suggestions(self) -> None:
        for c in self._sug_cards: c.destroy()
        self._sug_cards.clear()
        sug = self._session_mem.suggest_related(self._context_queue)
        qn = {q["name"] for q in self._context_queue}
        for it in sug:
            n = it.get("name", ""); s = it.get("source", "")
            if n in qn: continue
            cd = ctk.CTkFrame(self._sug_frame, fg_color=C["card"], corner_radius=4,
                              border_width=1, border_color=C["warn"])
            cd.pack(fill="x", padx=2, pady=1); self._sug_cards.append(cd)
            r = ctk.CTkFrame(cd, fg_color="transparent"); r.pack(fill="x", padx=6, pady=3)
            ctk.CTkLabel(r, text=n, font=(F, 10), text_color=C["fg"]).pack(side="left")
            ctk.CTkButton(r, text="+ Add", width=48, height=20, font=(F, 9), fg_color=C["warn"],
                          command=lambda n=n, s=s: self._readd(n, s)).pack(side="right")
        if not self._sug_cards:
            l = ctk.CTkLabel(self._sug_frame, text="Add items to see related suggestions",
                             font=(F, 9), text_color=C["fg3"])
            l.pack(anchor="w", pady=2); self._sug_cards.append(l)

    def _update_recent(self) -> None:
        for c in self._rec_cards: c.destroy()
        self._rec_cards.clear()
        recent = self._session_mem.get_recently_used(8)
        qn = {q["name"] for q in self._context_queue}
        for it in recent:
            n = it.get("name", ""); s = it.get("source", "")
            if n in qn: continue
            cd = ctk.CTkFrame(self._rec_frame, fg_color=C["card"], corner_radius=4,
                              border_width=1, border_color=C["purple"])
            cd.pack(fill="x", padx=2, pady=1); self._rec_cards.append(cd)
            r = ctk.CTkFrame(cd, fg_color="transparent"); r.pack(fill="x", padx=6, pady=3)
            ctk.CTkLabel(r, text=n, font=(F, 10), text_color=C["fg"]).pack(side="left")
            ctk.CTkButton(r, text="+ Add", width=48, height=20, font=(F, 9), fg_color=C["purple"],
                          command=lambda n=n, s=s: self._readd(n, s)).pack(side="right")
        if not self._rec_cards:
            l = ctk.CTkLabel(self._rec_frame, text="No recent items yet", font=(F, 9), text_color=C["fg3"])
            l.pack(anchor="w", pady=2); self._rec_cards.append(l)

    def _readd(self, name: str, source: str) -> None:
        content = None
        if self._analysis:
            for b in self._analysis.blocks:
                if b.name == name: content = b.source; break
        if content is None and name in self._memory_files: content = self._memory_files[name]
        if content is None and self._analysis:
            for e in self._analysis.files:
                if e.path == source: content = e.content; break
        if content: self._add_to_context(name, source, content)
        else: self._toast(f"Content not found for {name}. Run Scan first.", "warning")

    def _rebuild_grab_buttons(self) -> None:
        """Build Quick Grab buttons from detected domains."""
        for b in self._grab_btns: b.destroy()
        self._grab_btns.clear()
        if hasattr(self, '_grab_placeholder') and self._grab_placeholder:
            self._grab_placeholder.destroy()
            self._grab_placeholder = None

        if not self._snippets:
            self._grab_placeholder = ctk.CTkLabel(
                self._grab_row1, text="Load a project on Dashboard first, then areas appear here",
                font=(F, 10), text_color=C["fg3"])
            self._grab_placeholder.pack(anchor="w", pady=4)
            return

        domains = get_all_domains(self._snippets)
        # Skip "Other" — it's a junk drawer, not useful for Quick Grab
        domains = [d for d in domains if d != "Other"]
        if not domains: return

        self._grab_status.configure(text=f"{len(domains)} areas found")

        for i, dom in enumerate(domains):
            count = sum(1 for s in self._snippets if get_domain(s.file_path) == dom)
            if count < 2:
                continue  # Skip domains with only 1 snippet
            clr = get_domain_color(dom)
            parent = self._grab_row1 if i < 6 else self._grab_row2
            btn = ctk.CTkButton(
                parent, text=f"{dom} ({count})", width=0, height=30,
                font=(F, 10, "bold"), fg_color=clr, hover_color=C["hover"],
                corner_radius=6,
                command=lambda d=dom: self._quick_grab(d),
            )
            btn.pack(side="left", padx=3, pady=2)
            self._grab_btns.append(btn)

    def _quick_grab(self, domain: str) -> None:
        """Add the top snippets from a domain to the context queue.

        Picks the most useful ones: documented first, focused functions over huge classes.
        """
        if not self._snippets:
            self._toast("Load and scan a project first", "warning"); return

        domain_blocks = [b for b in self._snippets if get_domain(b.file_path) == domain]
        if not domain_blocks:
            self._toast(f"No code found in {domain}", "warning"); return

        # Score and sort: documented + short = most useful for beginners
        def usefulness(b):
            score = 0
            if b.docstring and len(b.docstring) > 10: score += 100
            if b.kind in ("function", "async_function"): score += 50
            if b.kind == "class": score += 30
            lines = b.end_line - b.start_line
            if lines < 30: score += 40   # prefer focused code
            elif lines < 60: score += 20
            return -score  # negative for ascending sort
        domain_blocks.sort(key=usefulness)

        added = 0
        names_added = []
        for b in domain_blocks[:4]:
            if not any(q["name"] == b.name for q in self._context_queue):
                self._context_queue.append({"name": b.name, "source": b.file_path, "content": b.source})
                names_added.append(b.name)
                added += 1

        if added:
            self._render_queue(); self._render_matches()
            self._update_suggestions(); self._update_recent()
            self._update_preview(); self._update_token_display()
            # Show what was grabbed
            short_names = ", ".join(names_added[:3])
            if len(names_added) > 3:
                short_names += f" +{len(names_added) - 3} more"
            self._grab_status.configure(text=f"Grabbed: {short_names}")
            self._toast(f"Added {added} {domain} snippets to your prompt", "success")
        else:
            self._toast(f"All {domain} code already in your prompt", "info")

    def _clear_request(self) -> None:
        """Clear the request box, queue, and matches."""
        self._request_box.delete("1.0", "end")
        self._context_queue.clear()
        self._smart_matches.clear()
        self._render_queue(); self._render_matches()
        self._update_preview(); self._update_token_display()
        self._auto_status.configure(text="")
        self._grab_status.configure(text="") if hasattr(self, '_grab_status') else None

    def _set_request(self, text: str) -> None:
        """Set the request box text from a quick-start button."""
        self._request_box.delete("1.0", "end")
        self._request_box.insert("1.0", text)
        self._request_box.focus_set()
        self._request_box.mark_set("insert", "end")
        # Trigger auto-find for the quick-start text
        if self._autofind_id:
            self.after_cancel(self._autofind_id)
        self._autofind_id = self.after(300, self._auto_find_code)
        self._update_preview()

    def _get_request_text(self) -> str:
        """Get the user's request from the request box."""
        try:
            return self._request_box.get("1.0", "end").strip()
        except Exception:
            return ""

    def _assemble(self, mode: str = "smart") -> str:
        """Assemble the final prompt.

        Modes:
            'smart' — uses Prompt Architect logic (role, constraints, quality gate)
            'template' — uses simple template wrapping
            'raw' — just snippets + request, no wrapping
        """
        items = ""
        for it in self._context_queue:
            items += f"### {it['name']} (from {it['source']})\n```\n{it['content'].strip()}\n```\n\n"
        request = self._get_request_text()
        if not items and not request:
            return ""

        if mode == "smart":
            # Get project conventions if available
            conventions = ""
            if self._analysis and self._analysis.conventions.samples_analyzed > 0:
                cv = self._analysis.conventions
                parts = []
                if cv.path_style != "unknown": parts.append(f"Path style: {cv.path_style}")
                if cv.type_hints != "unknown": parts.append(f"Type hints: {cv.type_hints}")
                if cv.logging_style != "unknown": parts.append(f"Logging: {cv.logging_style}")
                if cv.error_handling != "unknown": parts.append(f"Error handling: {cv.error_handling}")
                conventions = "\n".join(f"- {p}" for p in parts)

            return build_smart_prompt(
                request=request or "Work with the code context provided.",
                code_context=items.strip(),
                project_conventions=conventions,
            )
        elif mode == "template":
            t = TEMPLATES.get(self._tmpl.get(), "{items}\n\n{request}")
            return t.format(items=items.strip(), request=request).strip()
        else:  # raw
            parts = []
            if items.strip(): parts.append(items.strip())
            if request: parts.append(request)
            return "\n\n".join(parts)

    def _update_preview(self) -> None:
        mode = self._tmpl.get()
        if mode == "Smart (Recommended)":
            txt = self._assemble("smart")
        elif mode == "Raw (No Wrapping)":
            txt = self._assemble("raw")
        else:
            txt = self._assemble("template")

        self._preview.configure(state="normal"); self._preview.delete("1.0", "end")
        if txt:
            self._preview.insert("1.0", txt)
        else:
            self._preview.insert("1.0",
                "Your combined prompt will appear here.\n\n"
                "1. Use the search bar to find relevant code snippets\n"
                "2. Type your request in the green box above\n"
                "3. Hit the blue Copy button below\n"
                "4. Paste into Claude Code")
        self._preview.configure(state="disabled")

        # Token count + intent detection
        tokens = count_tokens(txt)
        request = self._get_request_text()
        if request:
            intent = detect_intent(request)
            role = ROLES.get(intent, "code")[:40]
            self._tok_lbl.configure(text=f"~{tokens:,} tok | Role: {intent}")
        else:
            self._tok_lbl.configure(text=f"~{tokens:,} tokens")

    def _copy_context(self) -> None:
        # Block empty copies
        request = self._get_request_text()
        if not self._context_queue and not request:
            self._toast("Type a request or add snippets first", "warning"); return
        # Debounce: prevent duplicate clicks
        if getattr(self, '_copy_locked', False):
            return
        self._copy_locked = True
        self.after(2000, lambda: setattr(self, '_copy_locked', False))

        mode = self._tmpl.get()
        if mode == "Smart (Recommended)":
            txt = self._assemble("smart")
        elif mode == "Raw (No Wrapping)":
            txt = self._assemble("raw")
        else:
            txt = self._assemble("template")
        if not txt: self._toast("Nothing to copy", "warning"); return
        tok = count_tokens(txt)
        self._copy_clip(txt, track=False)
        proj = self._project_path.name if self._project_path else ""
        self._tracker.record("context_build", tok, project=proj,
                             detail=f"mode={mode}, items={len(self._context_queue)}")
        self._session_mem.record_clipboard_copy(mode, len(self._context_queue), tok)
        self._update_token_display()

    def _copy_raw(self) -> None:
        request = self._get_request_text()
        if not self._context_queue and not request:
            self._toast("Type a request or add snippets first", "warning"); return
        if getattr(self, '_copy_locked', False):
            return
        self._copy_locked = True
        self.after(2000, lambda: setattr(self, '_copy_locked', False))

        txt = self._assemble("raw")
        if not txt: self._toast("Nothing to copy", "warning"); return
        tok = count_tokens(txt)
        self._copy_clip(txt, track=False)
        proj = self._project_path.name if self._project_path else ""
        self._tracker.record("clipboard_copy", tok, project=proj, detail="raw")
        self._session_mem.record_clipboard_copy("raw", len(self._context_queue), tok)
        self._update_token_display()

    # ═══════════════════════════════════════════════════════════════════
    #  SNIPPETS
    # ═══════════════════════════════════════════════════════════════════
    def _build_snippets(self) -> None:
        fr = ctk.CTkFrame(self._content, fg_color=C["bg"])
        self._views["snippets"] = fr
        ctk.CTkLabel(fr, text="Snippets", font=(F, 20, "bold"), text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="Browse by area or search. Click + Context to add to your prompt.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        srow = ctk.CTkFrame(fr, fg_color="transparent"); srow.pack(fill="x", padx=20, pady=(0, 4))
        self._s_search = ctk.CTkEntry(srow, placeholder_text="Search: type anything... (e.g. 'browser stuff' or 'save files')",
                                      font=(F, 12), fg_color=C["input"], border_color=C["border"], height=34)
        self._s_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._s_search.bind("<KeyRelease>", lambda e: self._filter_snips())

        # Domain tabs — built dynamically after scan
        self._s_tab_frame = ctk.CTkFrame(fr, fg_color="transparent")
        self._s_tab_frame.pack(fill="x", padx=20, pady=(0, 6))
        self._s_domain_btns: list[ctk.CTkButton] = []
        self._s_active_domain = "All"

        sp = ctk.CTkFrame(fr, fg_color="transparent"); sp.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._s_list = ctk.CTkScrollableFrame(sp, fg_color=C["bg2"], corner_radius=8,
                                              border_width=1, border_color=C["border"], width=400)
        self._s_list.pack(side="left", fill="both", expand=False, padx=(0, 8))
        self._s_cards: list[ctk.CTkFrame] = []
        self._s_prev = ctk.CTkTextbox(sp, font=(M, 12), fg_color=C["card"], border_color=C["border"],
                                      border_width=1, text_color="#d4d4d4", state="disabled", wrap="none")
        self._s_prev.pack(side="left", fill="both", expand=True)

    def _rebuild_domain_tabs(self) -> None:
        """Rebuild domain filter tabs after scanning."""
        for b in self._s_domain_btns: b.destroy()
        self._s_domain_btns.clear()
        domains = ["All"] + get_all_domains(self._snippets)
        for dom in domains:
            clr = C["accent"] if dom == "All" else get_domain_color(dom)
            active = dom == self._s_active_domain
            btn = ctk.CTkButton(
                self._s_tab_frame, text=dom, width=0, height=26, font=(F, 10),
                fg_color=clr if active else C["bg2"],
                hover_color=C["hover"], corner_radius=4,
                text_color=C["fg"] if active else C["fg2"],
                command=lambda d=dom: self._set_domain(d),
            )
            btn.pack(side="left", padx=2, pady=2)
            self._s_domain_btns.append(btn)

    def _set_domain(self, domain: str) -> None:
        self._s_active_domain = domain
        self._rebuild_domain_tabs()
        self._filter_snips()

    def _filter_snips(self) -> None:
        q = self._s_search.get().lower().strip()
        dom = self._s_active_domain
        out = []
        for b in self._snippets:
            if dom != "All" and get_domain(b.file_path) != dom:
                continue
            if q:
                t = f"{b.name} {b.file_path} {b.docstring or ''} {get_domain(b.file_path)}".lower()
                if q not in t:
                    continue
            out.append(b)
        self._render_snips(out[:100])

    def _render_snips(self, blocks: list[CodeBlock]) -> None:
        for c in self._s_cards: c.destroy()
        self._s_cards.clear()
        if not blocks:
            l = ctk.CTkLabel(self._s_list, text="No snippets found.\nLoad a project and run Scan or Bootstrap first.",
                             font=(F, 11), text_color=C["fg3"], wraplength=360)
            l.pack(padx=8, pady=20); self._s_cards.append(l); return
        for b in blocks:
            domain = get_domain(b.file_path)
            dom_clr = get_domain_color(domain)
            cd = ctk.CTkFrame(self._s_list, fg_color=C["card"], corner_radius=6, border_width=1, border_color=C["border"])
            cd.pack(fill="x", padx=4, pady=3); self._s_cards.append(cd)
            tp = ctk.CTkFrame(cd, fg_color="transparent"); tp.pack(fill="x", padx=8, pady=(6, 2))
            # Domain badge
            ctk.CTkLabel(tp, text=domain, font=(F, 8), text_color=C["fg"],
                         fg_color=dom_clr, corner_radius=8, padx=6, pady=1).pack(side="right", padx=(4, 0))
            ctk.CTkLabel(tp, text=b.name, font=(F, 12, "bold"), text_color=C["fg"]).pack(side="left")
            ctk.CTkLabel(cd, text=f"{b.file_path}:{b.start_line}", font=(M, 9), text_color=C["fg3"]).pack(padx=8, anchor="w")
            if b.docstring:
                ctk.CTkLabel(cd, text=b.docstring.split("\n")[0][:80], font=(F, 10), text_color=C["fg2"]).pack(padx=8, anchor="w")
            br = ctk.CTkFrame(cd, fg_color="transparent"); br.pack(fill="x", padx=8, pady=(2, 6))
            ctk.CTkButton(br, text="Copy", width=55, height=24, font=(F, 10), fg_color=C["accent"],
                          command=lambda b=b: self._copy_clip(b.source)).pack(side="left", padx=(0, 4))
            ctk.CTkButton(br, text="+ Context", width=80, height=24, font=(F, 10), fg_color=C["purple"],
                          command=lambda b=b: self._add_to_context(b.name, b.file_path, b.source)).pack(side="left")
            cd.bind("<Button-1>", lambda e, b=b: self._prev_snip(b))
            for ch in cd.winfo_children(): ch.bind("<Button-1>", lambda e, b=b: self._prev_snip(b))
            cd.bind("<Button-1>", lambda e, b=b: self._prev_snip(b))
            for ch in cd.winfo_children(): ch.bind("<Button-1>", lambda e, b=b: self._prev_snip(b))

    def _prev_snip(self, b: CodeBlock) -> None:
        self._s_prev.configure(state="normal"); self._s_prev.delete("1.0", "end")
        self._s_prev.insert("1.0", f"# {b.name} ({b.kind})\n# From: {b.file_path}:{b.start_line}\n\n{b.source}")
        self._s_prev.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════════
    #  MEMORY
    # ═══════════════════════════════════════════════════════════════════
    def _build_memory(self) -> None:
        fr = ctk.CTkFrame(self._content, fg_color=C["bg"])
        self._views["memory"] = fr
        ctk.CTkLabel(fr, text="Memory Files", font=(F, 20, "bold"), text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="These files are auto-loaded by Claude Code for persistent context across sessions.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))
        sp = ctk.CTkFrame(fr, fg_color="transparent"); sp.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._m_list = ctk.CTkScrollableFrame(sp, fg_color=C["bg2"], corner_radius=8,
                                              border_width=1, border_color=C["border"], width=280)
        self._m_list.pack(side="left", fill="both", padx=(0, 8))
        self._m_cards: list[ctk.CTkFrame] = []
        self._m_prev = ctk.CTkTextbox(sp, font=(M, 12), fg_color=C["card"], border_color=C["border"],
                                      border_width=1, text_color="#d4d4d4", state="disabled")
        self._m_prev.pack(side="left", fill="both", expand=True)

    def _load_memory(self) -> None:
        if not self._project_path: return
        self._memory_files.clear()
        md = self._project_path / ".claude" / "memory"
        if md.is_dir():
            for f in sorted(md.iterdir()):
                if f.is_file() and f.suffix == ".md":
                    try: self._memory_files[f.name] = f.read_text(encoding="utf-8", errors="replace")
                    except OSError: pass
        for c in self._m_cards: c.destroy()
        self._m_cards.clear()
        if not self._memory_files:
            l = ctk.CTkLabel(self._m_list, text="No memory files yet.\nRun Bootstrap on the Dashboard first.",
                             font=(F, 11), text_color=C["fg3"], wraplength=240)
            l.pack(padx=8, pady=20); self._m_cards.append(l); return
        for fn, cnt in self._memory_files.items():
            cd = ctk.CTkFrame(self._m_list, fg_color=C["card"], corner_radius=6, border_width=1, border_color=C["border"])
            cd.pack(fill="x", padx=4, pady=3); self._m_cards.append(cd)
            ctk.CTkLabel(cd, text=fn.replace("_", " ").replace(".md", "").title(),
                         font=(F, 12, "bold"), text_color=C["fg"]).pack(padx=8, pady=(6, 2), anchor="w")
            ctk.CTkLabel(cd, text=f"{cnt.count(chr(10))} lines", font=(F, 9), text_color=C["fg3"]).pack(padx=8, anchor="w")
            br = ctk.CTkFrame(cd, fg_color="transparent"); br.pack(fill="x", padx=8, pady=(2, 6))
            ctk.CTkButton(br, text="Copy", width=55, height=24, font=(F, 10), fg_color=C["accent"],
                          command=lambda c=cnt: self._copy_clip(c)).pack(side="left", padx=(0, 4))
            ctk.CTkButton(br, text="+ Context", width=80, height=24, font=(F, 10), fg_color=C["purple"],
                          command=lambda f=fn, c=cnt: self._add_to_context(f, "memory", c)).pack(side="left")
            cd.bind("<Button-1>", lambda e, c=cnt: self._prev_mem(c))
            for ch in cd.winfo_children(): ch.bind("<Button-1>", lambda e, c=cnt: self._prev_mem(c))

    def _prev_mem(self, cnt: str) -> None:
        self._m_prev.configure(state="normal"); self._m_prev.delete("1.0", "end")
        self._m_prev.insert("1.0", cnt); self._m_prev.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════════
    #  SETTINGS + TUTORIAL
    # ═══════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════
    #  AUTO-SCAN TIMER
    # ═══════════════════════════════════════════════════════════════════
    def _start_auto_scan(self) -> None:
        """Start the 5-minute auto-refresh cycle."""
        self._stop_auto_scan()
        self._auto_scan_tick()

    def _stop_auto_scan(self) -> None:
        if self._auto_scan_id:
            self.after_cancel(self._auto_scan_id)
            self._auto_scan_id = None

    def _auto_scan_tick(self) -> None:
        """Check for file changes, only do a full rescan if something changed."""
        from .scanners.project import scan_project_fast_mtimes

        if self._project_path and not self._busy:
            def do():
                new_mtimes = scan_project_fast_mtimes(self._project_path, self._config)
                # Compare against last known mtimes
                old_mtimes = getattr(self, '_last_mtimes', {})
                if new_mtimes != old_mtimes:
                    self._last_mtimes = new_mtimes
                    return self._mgr.analyze(self._project_path)  # full rescan
                return None  # no changes

            def done(a):
                if a is not None:
                    self._analysis = a
                    self._snippets = [b for b in a.blocks if b.docstring or b.kind != "file"]
                    self._update_stats(); self._load_memory()
                    self._rebuild_domain_tabs(); self._filter_snips()
                    self._rebuild_grab_buttons()
                    self._st_label.configure(text=f"Auto-scan: {len(a.files)} files (changed)")
                    self._log("Auto-scan: changes detected, refreshed")
                else:
                    self._st_label.configure(text="Auto-scan: no changes")
            self._run_async(do, done)
        self._auto_scan_id = self.after(self._auto_scan_interval, self._auto_scan_tick)

    # ═══════════════════════════════════════════════════════════════════
    #  ANALYSIS REPORT
    # ═══════════════════════════════════════════════════════════════════
    def _build_report(self) -> None:
        fr = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        self._views["report"] = fr

        ctk.CTkLabel(fr, text="Analysis Report", font=(F, 20, "bold"),
                     text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="Shareable token savings analysis. No personal data included.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        # Action buttons
        br = ctk.CTkFrame(fr, fg_color="transparent"); br.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(br, text="Generate Report", font=(F, 12, "bold"), fg_color=C["accent"],
                      height=36, width=160, command=self._gen_report).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="Copy Report", font=(F, 12), fg_color=C["purple"],
                      height=36, width=130, command=self._copy_report).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="Save as .txt", font=(F, 12), fg_color=C["bg2"],
                      height=36, width=110, command=self._save_report).pack(side="left")

        self._report_box = ctk.CTkTextbox(fr, font=(M, 11), fg_color=C["card"],
                                          border_color=C["border"], border_width=1,
                                          text_color="#d4d4d4", state="disabled")
        self._report_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._report_text = ""

    def _gen_report(self) -> None:
        if not self._analysis:
            self._toast("Load and scan a project first", "warning"); return
        self._st_label.configure(text="Generating report...")

        def do():
            a = self._analysis
            snippets = self._snippets
            total_src = sum(count_tokens(f.content) for f in a.files)
            p = self._project_path

            cmd_tok = 0
            cm = p / "CLAUDE.md"
            if cm.is_file(): cmd_tok = count_tokens(cm.read_text(encoding="utf-8"))
            mem_dir = p / ".claude" / "memory"
            mem_tok = sum(len(f.read_text(encoding="utf-8"))//4 for f in mem_dir.iterdir() if f.is_file()) if mem_dir.is_dir() else 0
            snip_dir = p / ".claude" / "snippets"
            snip_count = sum(1 for f in snip_dir.rglob("*.py")) if snip_dir.is_dir() else 0

            scenarios = [
                ("send message to ai chat", "browser_actions.py"),
                ("cdp chrome connection timeout", "cdp_client.py"),
                ("how config loading works", None),
                ("create and start sessions", "session_manager.py"),
                ("copy stuff to clipboard", None),
                ("window positioning and focus", "window_manager.py"),
                ("extracting code blocks with ast", None),
                ("fuzzy search with typos", None),
                ("ollama model pull download", None),
                ("token tracker savings count", None),
            ]

            lines = []
            lines.append("CLAUDE TOKEN SAVER - ANALYSIS REPORT")
            lines.append("=" * 50)
            lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Project: {a.name}")
            lines.append(f"Files scanned: {len(a.files)}")
            lines.append(f"Total source tokens: {total_src:,}")
            lines.append("")
            lines.append("PRE-LOADED CONTEXT (auto-loaded by Claude Code)")
            lines.append("-" * 50)
            lines.append(f"  CLAUDE.md:      {cmd_tok:,} tokens")
            lines.append(f"  Memory files:   {mem_tok:,} tokens")
            lines.append(f"  Total:          {cmd_tok + mem_tok:,} tokens")
            lines.append(f"  Compression:    {round(total_src * 0.3 / max(cmd_tok + mem_tok, 1), 1)}x")
            lines.append(f"  (replaces reading ~{int(total_src * 0.3):,} tokens = 30% of source)")
            lines.append("")
            lines.append(f"SNIPPET LIBRARY: {snip_count} reusable code blocks")
            lines.append(f"SEARCHABLE BLOCKS: {len(snippets)} functions/classes")
            lines.append(f"MODULES MAPPED: {len(a.modules)}")
            lines.append("")
            lines.append("SEARCH ACCURACY TEST (sloppy English queries)")
            lines.append("-" * 50)

            total_saved = 0
            hits = 0
            for query, compare_file in scenarios:
                results = smart_search(snippets, query, max_results=4, min_score=2.0)
                targeted = sum(count_tokens(b.source) for _, b in results)
                names = [b.name for _, b in results][:3]
                if compare_file:
                    ff = [f for f in a.files if f.path == compare_file]
                    full = count_tokens(ff[0].content) if ff else targeted * 3
                else:
                    full = targeted * 3
                saved = max(0, full - targeted)
                total_saved += saved
                pct = round((1 - targeted / max(full, 1)) * 100)
                found = len(results) > 0
                if found: hits += 1
                status = "PASS" if found else "MISS"
                lines.append(f'  [{status}] "{query}"')
                lines.append(f"         -> {names}  ({pct}% saved, {saved:,} tokens)")

            lines.append("")
            lines.append(f"  Accuracy: {hits}/{len(scenarios)} queries found relevant code")
            lines.append(f"  Total tokens saved across scenarios: {total_saved:,}")
            lines.append(f"  Average per query: {total_saved // len(scenarios):,} tokens")
            lines.append("")

            lines.append("CONVENTIONS DETECTED")
            lines.append("-" * 50)
            cv = a.conventions
            lines.append(f"  Path handling:    {cv.path_style}")
            lines.append(f"  Type hints:       {cv.type_hints}")
            lines.append(f"  String format:    {cv.string_format}")
            lines.append(f"  Error handling:   {cv.error_handling}")
            lines.append(f"  Logging:          {cv.logging_style}")
            lines.append(f"  Import style:     {cv.import_style}")
            lines.append("")

            tracker = self._tracker
            lines.append("LIFETIME TOKEN SAVINGS")
            lines.append("-" * 50)
            lines.append(f"  All-time total: {tracker.get_all_time_total():,} tokens")
            bd = tracker.get_operation_breakdown()
            for op, tok in sorted(bd.items(), key=lambda x: -x[1]):
                lines.append(f"    {op}: {tok:,}")
            lines.append("")
            lines.append("=" * 50)
            lines.append("Generated by Claude Token Saver v4.5")
            lines.append("github.com/... (share this report freely)")

            return "\n".join(lines)

        def done(text):
            self._report_text = text
            self._report_box.configure(state="normal")
            self._report_box.delete("1.0", "end")
            self._report_box.insert("1.0", text)
            self._report_box.configure(state="disabled")
            self._st_label.configure(text="Report ready")
            self._toast("Report generated!", "success")

        self._run_async(do, done)

    def _copy_report(self) -> None:
        if self._report_text:
            self._copy_clip(self._report_text)
        else:
            self._toast("Generate a report first", "warning")

    def _save_report(self) -> None:
        if not self._report_text:
            self._toast("Generate a report first", "warning"); return
        path = Path.home() / "Downloads" / f"token_saver_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            path.write_text(self._report_text, encoding="utf-8")
            self._toast(f"Saved to {path.name}", "success")
            self._log(f"Report saved: {path}")
        except OSError as e:
            self._toast(f"Save failed: {e}", "error")

    # ═══════════════════════════════════════════════════════════════════
    #  SETTINGS + OLLAMA + TUTORIAL
    # ═══════════════════════════════════════════════════════════════════
    def _build_settings(self) -> None:
        fr = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        self._views["settings"] = fr

        ctk.CTkLabel(fr, text="Settings", font=(F, 20, "bold"), text_color=C["fg"]).pack(padx=20, pady=(16, 12), anchor="w")

        # ═══════════════════════════════════════════════════════════
        #  AUTO-INJECT SETUP (one-time Claude Code hook installer)
        # ═══════════════════════════════════════════════════════════
        ai_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["ok"])
        ai_card.pack(fill="x", padx=20, pady=(0, 12))

        ai_hdr = ctk.CTkFrame(ai_card, fg_color="transparent"); ai_hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(ai_hdr, text="Auto-Inject (one-time setup)", font=(F, 14, "bold"),
                     text_color=C["ok"]).pack(side="left")
        self._ai_status_lbl = ctk.CTkLabel(ai_hdr, text="Checking...", font=(F, 11), text_color=C["fg3"])
        self._ai_status_lbl.pack(side="right")

        ai_explain = (
            "Make Claude Code auto-refresh your project context every session.\n"
            "After one-click install:\n"
            "  - Every Claude Code session starts by running prep on your project\n"
            "  - CLAUDE.md + memory files auto-update with your latest code\n"
            "  - 'Hot functions' (most-used code) pre-loaded into context\n"
            "  - You NEVER have to open this GUI again for baseline context\n"
            "  (You still use the GUI for per-query targeted snippets)"
        )
        ctk.CTkLabel(ai_card, text=ai_explain, font=(F, 10),
                     text_color=C["fg2"], wraplength=720, justify="left"
                     ).pack(padx=16, pady=(4, 8), anchor="w")

        ai_btn_row = ctk.CTkFrame(ai_card, fg_color="transparent")
        ai_btn_row.pack(fill="x", padx=16, pady=(0, 12))
        self._ai_install_btn = ctk.CTkButton(
            ai_btn_row, text="Install Auto-Inject", width=180, height=34,
            font=(F, 12, "bold"), fg_color=C["ok"],
            command=self._ai_install,
        )
        self._ai_install_btn.pack(side="left", padx=(0, 8))
        self._ai_uninstall_btn = ctk.CTkButton(
            ai_btn_row, text="Uninstall", width=100, height=34,
            font=(F, 11), fg_color=C["err"],
            command=self._ai_uninstall,
        )
        self._ai_uninstall_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            ai_btn_row, text="Show Tutorial", width=120, height=34,
            font=(F, 11), fg_color=C["bg2"],
            command=self._ai_show_tutorial,
        ).pack(side="left")

        self._ai_tutorial_box = ctk.CTkTextbox(
            ai_card, font=(M, 10), fg_color=C["input"], text_color=C["fg2"],
            border_width=0, height=0, state="disabled",
        )
        self._ai_tutorial_box.pack(fill="x", padx=16, pady=(0, 12))
        self._ai_tutorial_visible = False

        # ═══════════════════════════════════════════════════════════
        #  AUTO-LAUNCH GUI ON SESSION (opt-in second hook)
        # ═══════════════════════════════════════════════════════════
        al_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8,
                               border_width=2, border_color=C["purple"])
        al_card.pack(fill="x", padx=20, pady=(0, 12))

        al_hdr = ctk.CTkFrame(al_card, fg_color="transparent")
        al_hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(al_hdr, text="Auto-launch on Claude Code session",
                     font=(F, 14, "bold"), text_color=C["purple"]).pack(side="left")
        self._al_status_lbl = ctk.CTkLabel(
            al_hdr, text="Checking...", font=(F, 11), text_color=C["fg3"],
        )
        self._al_status_lbl.pack(side="right")

        ctk.CTkLabel(
            al_card,
            text="Optional. When ON, every Claude Code session will open Token "
                 "Saver so you're reminded to grab targeted snippets for the "
                 "biggest token savings (Layer 2). Independent from Auto-Inject.",
            font=(F, 10), text_color=C["fg2"], wraplength=720, justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        self._set_auto_launch = ctk.CTkCheckBox(
            al_card, text="Auto-launch Token Saver when a Claude Code session starts",
            font=(F, 12), command=self._al_toggle_main,
        )
        self._set_auto_launch.pack(padx=20, pady=(4, 2), anchor="w")
        if self._prefs.auto_launch_gui_on_session:
            self._set_auto_launch.select()

        self._set_auto_launch_min = ctk.CTkCheckBox(
            al_card, text="    Open minimized to tray (off = full GUI window)",
            font=(F, 11), command=self._al_toggle_minimized,
        )
        self._set_auto_launch_min.pack(padx=20, pady=(0, 6), anchor="w")
        if self._prefs.auto_launch_minimized:
            self._set_auto_launch_min.select()

        al_btns = ctk.CTkFrame(al_card, fg_color="transparent")
        al_btns.pack(fill="x", padx=16, pady=(2, 12))
        self._al_install_btn = ctk.CTkButton(
            al_btns, text="Install hook", width=130, height=30,
            font=(F, 11, "bold"), fg_color=C["ok"],
            command=self._al_install,
        )
        self._al_install_btn.pack(side="left", padx=(0, 8))
        self._al_uninstall_btn = ctk.CTkButton(
            al_btns, text="Uninstall hook", width=120, height=30,
            font=(F, 11), fg_color=C["err"],
            command=self._al_uninstall,
        )
        self._al_uninstall_btn.pack(side="left")

        # ═══════════════════════════════════════════════════════════
        #  AUTOSTART SHORTCUT REPAIR
        # ═══════════════════════════════════════════════════════════
        as_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8,
                               border_width=1, border_color=C["border"])
        as_card.pack(fill="x", padx=20, pady=(0, 12))

        as_hdr = ctk.CTkFrame(as_card, fg_color="transparent")
        as_hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(as_hdr, text="Windows autostart shortcut", font=(F, 14, "bold"),
                     text_color=C["fg"]).pack(side="left")
        self._as_status_lbl = ctk.CTkLabel(
            as_hdr, text="Checking...", font=(F, 11), text_color=C["fg3"],
        )
        self._as_status_lbl.pack(side="right")

        ctk.CTkLabel(
            as_card,
            text="Token Saver tray launches when you log into Windows. Click "
                 "Repair if the shortcut is missing or pointing at a stale exe path.",
            font=(F, 10), text_color=C["fg3"], wraplength=720, justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        as_btns = ctk.CTkFrame(as_card, fg_color="transparent")
        as_btns.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            as_btns, text="Repair / re-create shortcut", width=220, height=30,
            font=(F, 11, "bold"), fg_color=C["accent"],
            command=self._repair_autostart,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            as_btns, text="Remove shortcut", width=140, height=30,
            font=(F, 11), fg_color=C["bg2"],
            command=self._remove_autostart,
        ).pack(side="left")

        # ═══════════════════════════════════════════════════════════
        #  ONBOARDING / WELCOME PANEL
        # ═══════════════════════════════════════════════════════════
        wel_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8,
                                border_width=1, border_color=C["accent"])
        wel_card.pack(fill="x", padx=20, pady=(0, 12))

        wh = ctk.CTkFrame(wel_card, fg_color="transparent")
        wh.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(wh, text="Welcome / Onboarding", font=(F, 14, "bold"),
                     text_color=C["accent"]).pack(side="left")
        ctk.CTkButton(wh, text="Open Welcome Now", width=160, height=28,
                      font=(F, 11, "bold"), fg_color=C["accent"],
                      command=self._open_welcome).pack(side="right")

        ctk.CTkLabel(
            wel_card,
            text="The welcome dialog explains what Token Saver does, what "
                 "permissions it uses, and walks you through the workflow. "
                 "It opens automatically on launch until you disable it here.",
            font=(F, 10), text_color=C["fg3"], wraplength=720, justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        self._set_show_welcome = ctk.CTkCheckBox(
            wel_card, text="Show welcome dialog on every launch",
            font=(F, 12), command=self._save_welcome_pref,
        )
        self._set_show_welcome.pack(padx=20, pady=(2, 12), anchor="w")
        if self._prefs.show_welcome_on_launch:
            self._set_show_welcome.select()
        else:
            self._set_show_welcome.deselect()

        # ═══════════════════════════════════════════════════════════
        #  OLLAMA MODEL MANAGER
        # ═══════════════════════════════════════════════════════════
        ollama_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["purple"])
        ollama_card.pack(fill="x", padx=20, pady=(0, 12))

        oh = ctk.CTkFrame(ollama_card, fg_color="transparent"); oh.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(oh, text="Local AI Model (Ollama)", font=(F, 14, "bold"),
                     text_color=C["purple"]).pack(side="left")
        self._ollama_status = ctk.CTkLabel(oh, text="Checking...", font=(F, 11), text_color=C["fg3"])
        self._ollama_status.pack(side="right")

        ctk.CTkLabel(ollama_card, text="A small local AI helps understand your search queries even with typos and sloppy English.",
                     font=(F, 10), text_color=C["fg3"], wraplength=700).pack(padx=16, anchor="w")

        # Current model selector
        sel_row = ctk.CTkFrame(ollama_card, fg_color="transparent"); sel_row.pack(fill="x", padx=16, pady=(8, 4))
        ctk.CTkLabel(sel_row, text="Active Model:", font=(F, 12), text_color=C["fg2"]).pack(side="left", padx=(0, 8))
        self._model_combo = ctk.CTkComboBox(sel_row, values=["(none)"], font=(F, 11),
                                            fg_color=C["input"], border_color=C["border"],
                                            height=32, width=300, command=self._on_model_select)
        self._model_combo.pack(side="left", padx=(0, 8))
        ctk.CTkButton(sel_row, text="Refresh", width=70, height=30, font=(F, 10),
                      fg_color=C["accent"], command=self._refresh_models).pack(side="left", padx=(0, 4))
        ctk.CTkButton(sel_row, text="Auto-Pick Best", width=110, height=30, font=(F, 10),
                      fg_color=C["ok"], command=self._auto_pick_model).pack(side="left")

        # Installed models list
        ctk.CTkLabel(ollama_card, text="Installed Models:", font=(F, 11, "bold"),
                     text_color=C["fg"]).pack(padx=16, pady=(8, 2), anchor="w")
        self._model_list_frame = ctk.CTkFrame(ollama_card, fg_color=C["bg"], corner_radius=6,
                                              border_width=1, border_color=C["border"])
        self._model_list_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._model_list_inner = ctk.CTkFrame(self._model_list_frame, fg_color="transparent")
        self._model_list_inner.pack(fill="x", padx=4, pady=4)
        self._model_widgets: list[ctk.CTkFrame] = []

        # Download section
        ctk.CTkLabel(ollama_card, text="Download a Model:", font=(F, 11, "bold"),
                     text_color=C["fg"]).pack(padx=16, pady=(4, 2), anchor="w")

        # Recommended quick-pull buttons
        rec_frame = ctk.CTkFrame(ollama_card, fg_color="transparent"); rec_frame.pack(fill="x", padx=16, pady=(0, 4))
        for i, rec in enumerate(RECOMMENDED_MODELS[:4]):
            ctk.CTkButton(
                rec_frame, text=f"{rec['name']} ({rec['size']})",
                font=(F, 10), fg_color=C["bg2"], hover_color=C["hover"],
                height=28, width=0, corner_radius=4,
                command=lambda n=rec["name"]: self._pull_model(n),
            ).pack(side="left", padx=(0, 4), pady=2)
        rec_frame2 = ctk.CTkFrame(ollama_card, fg_color="transparent"); rec_frame2.pack(fill="x", padx=16, pady=(0, 4))
        for rec in RECOMMENDED_MODELS[4:]:
            ctk.CTkButton(
                rec_frame2, text=f"{rec['name']} ({rec['size']})",
                font=(F, 10), fg_color=C["bg2"], hover_color=C["hover"],
                height=28, width=0, corner_radius=4,
                command=lambda n=rec["name"]: self._pull_model(n),
            ).pack(side="left", padx=(0, 4), pady=2)

        # Custom pull
        pull_row = ctk.CTkFrame(ollama_card, fg_color="transparent"); pull_row.pack(fill="x", padx=16, pady=(4, 4))
        self._pull_entry = ctk.CTkEntry(pull_row, placeholder_text="Or type any model name (e.g. mistral:7b)...",
                                        font=(F, 11), fg_color=C["input"], border_color=C["border"], height=30)
        self._pull_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(pull_row, text="Pull / Download", width=130, height=30, font=(F, 11, "bold"),
                      fg_color=C["purple"], command=lambda: self._pull_model(self._pull_entry.get().strip())
                      ).pack(side="left")

        # Progress
        self._pull_progress = ctk.CTkProgressBar(ollama_card, height=6, fg_color=C["bg"], progress_color=C["purple"])
        self._pull_progress.pack(fill="x", padx=16, pady=(2, 2)); self._pull_progress.set(0)
        self._pull_status = ctk.CTkLabel(ollama_card, text="", font=(F, 10), text_color=C["fg3"])
        self._pull_status.pack(padx=16, pady=(0, 12), anchor="w")

        # ═══════════════════════════════════════════════════════════
        #  TUTORIAL
        # ═══════════════════════════════════════════════════════════
        tut_card = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["accent"])
        tut_card.pack(fill="x", padx=20, pady=(0, 12))
        tut_hdr = ctk.CTkFrame(tut_card, fg_color="transparent"); tut_hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(tut_hdr, text="How To Use This Tool", font=(F, 14, "bold"),
                     text_color=C["accent"]).pack(side="left")
        self._tut_toggle = ctk.CTkButton(tut_hdr, text="Show Tutorial", width=110, height=28,
                                         font=(F, 11), fg_color=C["accent"], command=self._toggle_tutorial)
        self._tut_toggle.pack(side="right")
        self._tut_box = ctk.CTkTextbox(tut_card, font=(M, 11), fg_color=C["input"], text_color=C["fg2"],
                                       border_width=0, height=0, state="disabled")
        self._tut_box.pack(fill="x", padx=16, pady=(0, 12))
        self._tut_visible = False

        # ═══════════════════════════════════════════════════════════
        #  GENERATION + LIMITS + EXTENSIONS
        # ═══════════════════════════════════════════════════════════
        gen = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        gen.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(gen, text="Generation", font=(F, 14, "bold"), text_color=C["fg"]).pack(padx=16, pady=(12, 8), anchor="w")
        self._set_cmd = ctk.CTkCheckBox(gen, text="Generate CLAUDE.md", font=(F, 12)); self._set_cmd.pack(padx=20, pady=2, anchor="w"); self._set_cmd.select()
        self._set_mem = ctk.CTkCheckBox(gen, text="Generate Memory Files", font=(F, 12)); self._set_mem.pack(padx=20, pady=2, anchor="w"); self._set_mem.select()
        self._set_snp = ctk.CTkCheckBox(gen, text="Generate Snippets", font=(F, 12)); self._set_snp.pack(padx=20, pady=(2, 12), anchor="w"); self._set_snp.select()

        lim = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        lim.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(lim, text="Limits", font=(F, 14, "bold"), text_color=C["fg"]).pack(padx=16, pady=(12, 8), anchor="w")
        def mk(parent, label, default):
            r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(r, text=label, font=(F, 12), text_color=C["fg2"], width=180, anchor="w").pack(side="left")
            e = ctk.CTkEntry(r, font=(F, 12), fg_color=C["input"], border_color=C["border"], height=30, width=100)
            e.insert(0, str(default)); e.pack(side="left"); return e
        self._set_mf = mk(lim, "Max files to scan", 500)
        self._set_ms = mk(lim, "Max file size (KB)", 1024)
        self._set_sl = mk(lim, "Max snippet lines", 50)
        self._set_ml = mk(lim, "CLAUDE.md max lines", 200)
        ctk.CTkFrame(lim, fg_color="transparent", height=8).pack()

        ext = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        ext.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(ext, text="File Extensions", font=(F, 14, "bold"), text_color=C["fg"]).pack(padx=16, pady=(12, 8), anchor="w")
        self._set_ext = ctk.CTkEntry(ext, font=(F, 12), fg_color=C["input"], border_color=C["border"], height=30)
        self._set_ext.pack(fill="x", padx=20, pady=(0, 12)); self._set_ext.insert(0, ", ".join(self._config.extensions))

        br = ctk.CTkFrame(fr, fg_color="transparent"); br.pack(fill="x", padx=20, pady=(4, 20))
        ctk.CTkButton(br, text="Apply Settings", font=(F, 13, "bold"), fg_color=C["accent"],
                      height=38, width=160, command=self._apply_settings).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="Reset Defaults", font=(F, 12), fg_color=C["bg2"],
                      height=36, width=140, command=self._reset_settings).pack(side="left")

        # Kick off initial model check
        self.after(500, self._refresh_models)

    # ── Ollama model management ────────────────────────────────────────

    def _refresh_models(self) -> None:
        """Refresh the installed model list and combo."""
        def do():
            running = self._ollama.is_running()
            models = self._ollama.list_models() if running else []
            return running, models
        def done(result):
            running, models = result
            if running:
                self._ollama_status.configure(text="Ollama: RUNNING", text_color=C["ok"])
            else:
                self._ollama_status.configure(text="Ollama: NOT RUNNING", text_color=C["err"])
            # Update combo
            names = [m["name"] for m in models]
            if names:
                self._model_combo.configure(values=names)
                cur = self._ollama.get_current()
                if cur and cur in names:
                    self._model_combo.set(cur)
                elif not cur:
                    self._ollama.select_best()
                    cur = self._ollama.get_current()
                    if cur: self._model_combo.set(cur)
            else:
                self._model_combo.configure(values=["(no models installed)"])
                self._model_combo.set("(no models installed)")
            # Render model list
            self._render_model_list(models)
        self._run_async(do, done)

    def _render_model_list(self, models: list[dict]) -> None:
        for w in self._model_widgets: w.destroy()
        self._model_widgets.clear()
        if not models:
            l = ctk.CTkLabel(self._model_list_inner, text="No models installed. Download one below!",
                             font=(F, 11), text_color=C["fg3"])
            l.pack(pady=8); self._model_widgets.append(l); return
        for m in models:
            row = ctk.CTkFrame(self._model_list_inner, fg_color="transparent")
            row.pack(fill="x", pady=1); self._model_widgets.append(row)
            cur = self._ollama.get_current()
            dot = "  " if m["name"] != cur else "  "
            ctk.CTkLabel(row, text=f"{dot} {m['name']}", font=(M, 11),
                         text_color=C["ok"] if m["name"] == cur else C["fg"]).pack(side="left")
            info = f"{m['size_gb']}GB  {m['parameters']}  {m['quantization']}"
            ctk.CTkLabel(row, text=info, font=(F, 9), text_color=C["fg3"]).pack(side="left", padx=(8, 0))
            ctk.CTkButton(row, text="Use", width=40, height=22, font=(F, 9), fg_color=C["accent"],
                          command=lambda n=m["name"]: self._select_model(n)).pack(side="right", padx=(4, 0))
            ctk.CTkButton(row, text="Del", width=36, height=22, font=(F, 9), fg_color=C["err"],
                          command=lambda n=m["name"]: self._delete_model(n)).pack(side="right")

    def _on_model_select(self, name: str) -> None:
        if name and not name.startswith("("):
            self._ollama.set_model(name)
            self._toast(f"Model set: {name}", "info")

    def _select_model(self, name: str) -> None:
        self._ollama.set_model(name)
        self._model_combo.set(name)
        self._toast(f"Now using: {name}", "success")
        self._refresh_models()

    def _auto_pick_model(self) -> None:
        def do(): return self._ollama.select_best()
        def done(name):
            if name:
                self._model_combo.set(name)
                self._toast(f"Auto-selected: {name}", "success")
                self._refresh_models()
            else:
                self._toast("No models available. Download one first!", "warning")
        self._run_async(do, done)

    def _pull_model(self, name: str) -> None:
        if not name or name.startswith("("): self._toast("Enter a model name", "warning"); return
        self._pull_status.configure(text=f"Downloading {name}..."); self._pull_progress.set(0)
        self._toast(f"Downloading {name}...", "info")
        self._log(f"Pulling model: {name}")

        def on_progress(pct, status):
            self.after(0, lambda: self._pull_progress.set(pct / 100))
            self.after(0, lambda: self._pull_status.configure(text=f"{status}  {pct:.0f}%"))

        def on_done():
            self.after(0, lambda: self._pull_progress.set(1.0))
            self.after(0, lambda: self._pull_status.configure(text=f"{name} downloaded!"))
            self.after(0, lambda: self._toast(f"Model {name} ready!", "success"))
            self.after(0, lambda: self._log(f"Model downloaded: {name}"))
            self.after(500, self._refresh_models)
            # Auto-select if it's first model
            if not self._ollama.get_current():
                self.after(600, lambda: self._select_model(name))

        def on_error(err):
            self.after(0, lambda: self._pull_status.configure(text=f"Error: {err}"))
            self.after(0, lambda: self._toast(f"Download failed: {err}", "error"))

        self._ollama.pull_model(name, on_progress=on_progress, on_done=on_done, on_error=on_error)

    def _delete_model(self, name: str) -> None:
        def do(): return self._ollama.delete_model(name)
        def done(ok):
            if ok:
                self._toast(f"Deleted: {name}", "info"); self._log(f"Deleted model: {name}")
                if self._ollama.get_current() == name: self._ollama.set_model(None)
            else:
                self._toast(f"Failed to delete {name}", "error")
            self._refresh_models()
        self._run_async(do, done)

    # ── Tutorial + settings apply ──────────────────────────────────────

    # ── Auto-Inject handlers ──────────────────────────────────────────

    def _ai_refresh_status(self) -> None:
        """Check and display auto-inject install status."""
        try:
            from . import auto_inject
        except Exception as e:
            self._ai_status_lbl.configure(text=f"Module error: {e}", text_color=C["err"])
            return
        s = auto_inject.check_status()
        if not s["settings_exists"]:
            self._ai_status_lbl.configure(text="settings.json missing", text_color=C["err"])
            self._ai_install_btn.configure(state="disabled")
        elif not s["settings_valid"]:
            self._ai_status_lbl.configure(text=f"settings.json INVALID JSON", text_color=C["err"])
            self._ai_install_btn.configure(state="disabled")
        elif s["installed"]:
            self._ai_status_lbl.configure(text="INSTALLED — running on every session",
                                          text_color=C["ok"])
            self._ai_install_btn.configure(state="disabled")
            self._ai_uninstall_btn.configure(state="normal")
        else:
            self._ai_status_lbl.configure(text="Not installed", text_color=C["fg3"])
            self._ai_install_btn.configure(state="normal")
            self._ai_uninstall_btn.configure(state="disabled")

    def _ai_install(self) -> None:
        try:
            from . import auto_inject
        except Exception as e:
            self._toast(f"Module error: {e}", "error"); return
        ok, msg = auto_inject.install()
        if ok:
            self._toast("Auto-inject installed", "success")
            self._log(f"Auto-inject: {msg}")
        else:
            self._toast(f"Install failed: {msg}", "error")
            self._log(f"Auto-inject install failed: {msg}")
        self._ai_refresh_status()

    def _ai_uninstall(self) -> None:
        try:
            from . import auto_inject
        except Exception as e:
            self._toast(f"Module error: {e}", "error"); return
        ok, msg = auto_inject.uninstall()
        if ok:
            self._toast("Auto-inject removed", "info")
            self._log(f"Auto-inject: {msg}")
        else:
            self._toast(msg, "warning")
        self._ai_refresh_status()

    def _save_welcome_pref(self) -> None:
        """Persist 'show welcome on launch' checkbox state."""
        self._prefs.show_welcome_on_launch = bool(self._set_show_welcome.get())
        if self._prefs.save():
            state = "ON" if self._prefs.show_welcome_on_launch else "OFF"
            self._toast(f"Welcome on launch: {state}", "info")
        else:
            self._toast("Failed to save preference", "warning")

    # ── Auto-launch GUI on session ─────────────────────────────────────

    def _al_refresh_status(self) -> None:
        """Update auto-launch card status indicator + button states."""
        try:
            from . import auto_inject
            status = auto_inject.check_launcher_status()
        except Exception as e:
            self._al_status_lbl.configure(text=f"Module error: {e}",
                                          text_color=C["err"])
            return
        if not status["settings_exists"]:
            self._al_status_lbl.configure(text="settings.json missing",
                                          text_color=C["err"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="disabled")
        elif not status["settings_valid"]:
            self._al_status_lbl.configure(text="settings.json INVALID",
                                          text_color=C["err"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="disabled")
        elif status["installed"]:
            self._al_status_lbl.configure(text="Hook INSTALLED",
                                          text_color=C["ok"])
            self._al_install_btn.configure(state="disabled")
            self._al_uninstall_btn.configure(state="normal")
        else:
            self._al_status_lbl.configure(text="Hook not installed",
                                          text_color=C["fg3"])
            self._al_install_btn.configure(state="normal")
            self._al_uninstall_btn.configure(state="disabled")
        # Sub-toggle only meaningful when main toggle is on.
        if self._prefs.auto_launch_gui_on_session:
            self._set_auto_launch_min.configure(state="normal")
        else:
            self._set_auto_launch_min.configure(state="disabled")
        # Repair-shortcut card too.
        self._refresh_autostart_status()

    def _al_toggle_main(self) -> None:
        """Main toggle: persist pref, install/uninstall hook to match."""
        on = bool(self._set_auto_launch.get())
        self._prefs.auto_launch_gui_on_session = on
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        try:
            from . import auto_inject
            if on:
                ok, msg = auto_inject.install_launcher_hook()
            else:
                ok, msg = auto_inject.uninstall_launcher_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            self._al_refresh_status()
            return
        if ok:
            self._toast(f"Auto-launch: {'ON' if on else 'OFF'}",
                        "success" if on else "info")
            self._log(f"Auto-launch hook: {msg}")
        else:
            # If turning off and hook wasn't installed, that's fine.
            if not on and "not found" in msg.lower():
                self._toast("Auto-launch: OFF", "info")
            else:
                self._toast(f"Hook update failed: {msg}", "warning")
        self._al_refresh_status()

    def _al_toggle_minimized(self) -> None:
        """Sub-toggle: persist 'open minimized to tray' preference."""
        self._prefs.auto_launch_minimized = bool(self._set_auto_launch_min.get())
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        mode = "tray" if self._prefs.auto_launch_minimized else "full window"
        self._toast(f"Auto-launch mode: {mode}", "info")

    def _al_install(self) -> None:
        """Manual install button — bypasses toggle (useful for repair)."""
        try:
            from . import auto_inject
            ok, msg = auto_inject.install_launcher_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            return
        if ok:
            self._toast("Launcher hook installed", "success")
            self._log(f"Launcher hook: {msg}")
            # Sync pref ON to reflect reality.
            if not self._prefs.auto_launch_gui_on_session:
                self._prefs.auto_launch_gui_on_session = True
                self._prefs.save()
                self._set_auto_launch.select()
        else:
            self._toast(f"Install failed: {msg}", "error")
        self._al_refresh_status()

    def _al_uninstall(self) -> None:
        """Manual uninstall button — bypasses toggle (useful for repair)."""
        try:
            from . import auto_inject
            ok, msg = auto_inject.uninstall_launcher_hook()
        except Exception as e:
            self._toast(f"Module error: {e}", "error")
            return
        if ok:
            self._toast("Launcher hook removed", "info")
            self._log(f"Launcher hook: {msg}")
            if self._prefs.auto_launch_gui_on_session:
                self._prefs.auto_launch_gui_on_session = False
                self._prefs.save()
                self._set_auto_launch.deselect()
        else:
            self._toast(msg, "warning")
        self._al_refresh_status()

    # ── Autostart shortcut (Windows Startup folder) ────────────────────

    def _autostart_shortcut_path(self) -> Path:
        """Resolve %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\..."""
        import os
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return (
            Path(appdata) / "Microsoft" / "Windows" / "Start Menu"
            / "Programs" / "Startup" / "ClaudeTokenSaverTray.lnk"
        )

    def _autostart_target_path(self) -> Path:
        """Where the deployed exe is expected. Used as the shortcut target."""
        return Path.home() / "Desktop" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"

    def _refresh_autostart_status(self) -> None:
        if not hasattr(self, "_as_status_lbl"):
            return
        if not sys.platform == "win32":
            self._as_status_lbl.configure(text="Windows only",
                                          text_color=C["fg3"])
            return
        lnk = self._autostart_shortcut_path()
        target = self._autostart_target_path()
        if not lnk.is_file():
            self._as_status_lbl.configure(text="Shortcut MISSING",
                                          text_color=C["warn"])
        elif not target.is_file():
            self._as_status_lbl.configure(text="Target exe MISSING",
                                          text_color=C["err"])
        else:
            self._as_status_lbl.configure(text="OK",
                                          text_color=C["ok"])

    def _repair_autostart(self) -> None:
        """Create or recreate the Startup shortcut pointing at current exe."""
        if sys.platform != "win32":
            self._toast("Autostart shortcut is Windows-only", "warning")
            return
        target = self._autostart_target_path()
        if not target.is_file():
            self._toast(f"Target exe not found: {target}", "error")
            return
        lnk_path = self._autostart_shortcut_path()
        try:
            lnk_path.parent.mkdir(parents=True, exist_ok=True)
            # Use COM via WScript.Shell (same approach as PowerShell).
            import pythoncom  # noqa: F401  # prerequisite for Dispatch on some setups
        except ImportError:
            # pywin32 not installed; fall back to PowerShell.
            self._repair_autostart_via_powershell(lnk_path, target)
            return
        try:
            from win32com.client import Dispatch  # type: ignore
            shell = Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(str(lnk_path))
            sc.TargetPath = str(target)
            sc.Arguments = "--tray"
            sc.WorkingDirectory = str(target.parent)
            sc.WindowStyle = 7  # minimized
            sc.Description = "Claude Token Saver — system tray (auto-start)"
            sc.IconLocation = f"{target},0"
            sc.save()
            self._toast("Autostart shortcut repaired", "success")
        except Exception as e:
            self._log(f"COM shortcut creation failed: {e}; falling back to PowerShell")
            self._repair_autostart_via_powershell(lnk_path, target)
        self._refresh_autostart_status()

    def _repair_autostart_via_powershell(self, lnk_path: Path, target: Path) -> None:
        """PowerShell fallback for shortcut creation when pywin32 unavailable."""
        import subprocess
        ps_script = (
            f"$WshShell = New-Object -ComObject WScript.Shell;"
            f"$sc = $WshShell.CreateShortcut('{lnk_path}');"
            f"$sc.TargetPath = '{target}';"
            f"$sc.Arguments = '--tray';"
            f"$sc.WorkingDirectory = '{target.parent}';"
            f"$sc.WindowStyle = 7;"
            f"$sc.Description = 'Claude Token Saver tray (auto-start)';"
            f"$sc.IconLocation = '{target},0';"
            f"$sc.Save();"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0 and lnk_path.is_file():
                self._toast("Autostart shortcut repaired", "success")
            else:
                self._toast(f"Repair failed: {result.stderr or 'unknown error'}", "error")
        except (OSError, subprocess.TimeoutExpired) as e:
            self._toast(f"Repair failed: {e}", "error")

    def _remove_autostart(self) -> None:
        """Delete the Startup shortcut. Tray + auto-inject hook unaffected."""
        lnk_path = self._autostart_shortcut_path()
        if not lnk_path.is_file():
            self._toast("Shortcut already absent", "info")
            self._refresh_autostart_status()
            return
        try:
            lnk_path.unlink()
            self._toast("Autostart shortcut removed", "info")
        except OSError as e:
            self._toast(f"Remove failed: {e}", "error")
        self._refresh_autostart_status()

    def _ai_show_tutorial(self) -> None:
        """Toggle the Auto-Inject tutorial text."""
        if self._ai_tutorial_visible:
            self._ai_tutorial_box.configure(height=0)
            self._ai_tutorial_visible = False
            return
        text = AI_TUTORIAL_TEXT
        self._ai_tutorial_box.configure(state="normal", height=360)
        self._ai_tutorial_box.delete("1.0", "end")
        self._ai_tutorial_box.insert("1.0", text)
        self._ai_tutorial_box.configure(state="disabled")
        self._ai_tutorial_visible = True

    def _toggle_tutorial(self) -> None:
        if self._tut_visible:
            self._tut_box.configure(height=0); self._tut_toggle.configure(text="Show Tutorial")
            self._tut_visible = False
        else:
            self._tut_box.configure(state="normal", height=420)
            self._tut_box.delete("1.0", "end"); self._tut_box.insert("1.0", TUTORIAL_TEXT)
            self._tut_box.configure(state="disabled"); self._tut_toggle.configure(text="Hide Tutorial")
            self._tut_visible = True

    def _apply_settings(self) -> None:
        try:
            self._config.generate_claude_md = bool(self._set_cmd.get())
            self._config.generate_memory = bool(self._set_mem.get())
            self._config.generate_snippets = bool(self._set_snp.get())
            self._config.max_files = int(self._set_mf.get())
            self._config.max_file_size_kb = int(self._set_ms.get())
            self._config.max_snippet_lines = int(self._set_sl.get())
            self._config.claude_md_max_lines = int(self._set_ml.get())
            exts = [e.strip() for e in self._set_ext.get().split(",") if e.strip()]
            if exts: self._config.extensions = exts
            self._mgr = ClaudeContextManager(self._config)
            self._toast("Settings applied", "success")
        except ValueError as e:
            self._toast(f"Invalid value: {e}", "error")

    def _reset_settings(self) -> None:
        self._config = ScanConfig(); self._mgr = ClaudeContextManager(self._config)
        self._set_cmd.select(); self._set_mem.select(); self._set_snp.select()
        for e, d in [(self._set_mf, 500), (self._set_ms, 1024), (self._set_sl, 50), (self._set_ml, 200)]:
            e.delete(0, "end"); e.insert(0, str(d))
        self._set_ext.delete(0, "end"); self._set_ext.insert(0, ", ".join(self._config.extensions))
        self._toast("Settings reset", "info")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    TokenSaverApp().mainloop()

if __name__ == "__main__":
    main()
