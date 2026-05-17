"""Floating overlay button for Claude Desktop (Phase 2).

Tiny CTk Toplevel pinned always-on-top with no titlebar. User drags to
position next to Claude Desktop's input area; double-click to lock.
Position is persisted to prefs.

Click handler:
  1. Sends Ctrl+A then Ctrl+C to whatever window currently has focus
     (Claude Desktop must be focused — overlay clicks shouldn't take it).
  2. Reads clipboard via pyperclip.
  3. Renders a tiny project-picker popup.
  4. POSTs to http://127.0.0.1:7321/improve.

Caveat: overlay is a separate Win32 window. It does NOT auto-track
Claude Desktop's position. User positions it once and leaves it.
Window-following is deferred (out of scope per design doc).
"""

from __future__ import annotations

import json
import logging
import threading
import time
import tkinter as tk
import urllib.request
from pathlib import Path

import customtkinter as ctk

try:
    import pyperclip
except ImportError:
    pyperclip = None  # type: ignore[assignment]

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # don't quit on corner-mouse
except ImportError:
    pyautogui = None  # type: ignore[assignment]

# Win32 user32 — used for picker positioning, foreground-window
# save/restore around Ctrl+A+Ctrl+C macro, and AllowSetForegroundWindow
# to grant the GUI process permission to raise. All calls are guarded
# so non-Windows builds and missing-DLL paths degrade silently.
try:
    import ctypes
    _user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    _WIN32_OK = True
except (ImportError, OSError, AttributeError):
    _user32 = None  # type: ignore[assignment]
    _WIN32_OK = False

from .prefs import Prefs

logger = logging.getLogger(__name__)

_C = {
    "bg": "#1a1a1a", "card": "#212121", "input": "#1e1e1e",
    "fg": "#ffffff", "fg2": "#b0b0b0", "fg3": "#808080",
    "border": "#404040", "accent": "#0078d4",
    "ok": "#107c10", "warn": "#ff8c00", "err": "#e81123",
    "purple": "#8e44ad",
}

_OVERLAY_W = 130
_OVERLAY_H = 40

# Project picker dimensions + edge clamp constants. The picker is a
# borderless CTkToplevel anchored relative to the overlay; without
# clamping it can render off-screen if the overlay is at a screen edge.
_PICKER_W = 340
# Tall enough to show ~10 two-line project rows without scrolling.
# CTkScrollableFrame still kicks in if /projects ever exceeds the cap.
_PICKER_H = 460
_PICKER_GAP = 6        # gap between overlay and picker
_SCREEN_MARGIN = 8     # min distance from any screen edge

# Tightened HWND poll cadence so click-time foreground tracking doesn't
# lag the user. Cheap — one ctypes call per tick.
_FOREGROUND_POLL_MS = 150

# v0.5 — auto-fade so the overlay isn't visually loud all the time.
# The window is always-on-top (otherwise it's invisible behind whatever
# the user's typing into), so we instead fade its alpha when the
# cursor isn't nearby. Polled — Tk has no native cursor-leave for
# borderless overrideredirect windows.
_FADE_IDLE_ALPHA = 0.30           # how see-through when idle
_FADE_ACTIVE_ALPHA = 1.0
_FADE_PROXIMITY_PX = 120          # cursor within this → restore
_FADE_POLL_MS = 400               # how often we check the cursor
_FADE_DELAY_MS = 4000             # ms after last proximity → fade out


class OverlayButton(ctk.CTkToplevel):
    """Always-on-top floating button. Owned by the GUI app's lifetime."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self._parent = parent
        self._prefs = Prefs.load()
        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._locked = False
        # Fade state: ms-since-epoch of last time cursor was near.
        self._last_proximity_ms = 0
        self._current_alpha = _FADE_ACTIVE_ALPHA
        self._fade_job: str | None = None
        # Most recent foreground HWND that's NOT us — captured on every
        # proximity poll tick so a click can restore focus to the
        # window the user was actually typing in (e.g. Chrome) before
        # firing the Ctrl+A+Ctrl+C macro. Without this the macro
        # would hit our own borderless overlay window.
        self._last_external_hwnd: int = 0

        self.title("Token Saver Overlay")
        self.overrideredirect(True)  # no titlebar / borders
        self.attributes("-topmost", True)
        self.geometry(f"{_OVERLAY_W}x{_OVERLAY_H}")
        self.configure(fg_color=_C["card"])

        # Restore position; default = top-right of screen
        x, y = self._restore_position()
        self.geometry(f"{_OVERLAY_W}x{_OVERLAY_H}+{x}+{y}")

        self._build()

        # Allow drag-to-move on the frame, double-click to lock
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)
        self.bind("<Double-Button-1>", self._toggle_lock)

        # Start the proximity-fade poller after the window has rendered.
        # We mark proximity initially so the user sees the button at full
        # opacity when it first appears — fading in cold would be ugly.
        self._last_proximity_ms = int(time.time() * 1000)
        self.after(_FADE_POLL_MS, self._poll_proximity)

    def _restore_position(self) -> tuple[int, int]:
        """Get saved position or default to top-right of primary monitor."""
        pos = self._prefs.overlay_position or [0, 0]
        if pos and pos != [0, 0]:
            return int(pos[0]), int(pos[1])
        # Default: top-right corner with 24px margin
        try:
            sw = self.winfo_screenwidth()
            return sw - _OVERLAY_W - 24, 24
        except Exception:
            return 100, 100

    def _save_position(self) -> None:
        """Persist current position to prefs."""
        try:
            x = self.winfo_x()
            y = self.winfo_y()
            self._prefs.overlay_position = [x, y]
            self._prefs.save()
        except Exception as e:
            logger.debug("Failed to save overlay position: %s", e)

    def _build(self) -> None:
        # Outer Toplevel acts as the "border": fg_color is the border color.
        # Inner frame holds the button and is shrunk 2px on each side via
        # pack padding so the purple shows around the edges. (CustomTkinter
        # rejects negative width/height in .place(), so use pack instead.)
        border_color = _C["purple"]
        self.configure(fg_color=border_color)
        inner = ctk.CTkFrame(self, fg_color=_C["card"], corner_radius=6)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        btn = ctk.CTkButton(
            inner,
            text="🪄 Improve",
            font=("Segoe UI", 12, "bold"),
            fg_color=_C["purple"],
            hover_color="#6d2d8e",
            text_color="#ffffff",
            corner_radius=4,
            height=28,
            command=self._on_click,
        )
        btn.pack(fill="both", expand=True, padx=4, pady=4)
        # Drag bindings on button too (else clicking the button would always fire)
        btn.bind("<Button-1>", self._on_drag_start, add="+")
        btn.bind("<B1-Motion>", self._on_drag_motion, add="+")
        btn.bind("<ButtonRelease-1>", self._on_drag_end, add="+")
        btn.bind("<Double-Button-1>", self._toggle_lock, add="+")

    # ── Drag handling ─────────────────────────────────────────────

    def _on_drag_start(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._locked:
            return
        self._drag_data["x"] = event.x_root - self.winfo_x()
        self._drag_data["y"] = event.y_root - self.winfo_y()
        self._drag_data["moved"] = False

    def _on_drag_motion(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._locked:
            return
        nx = event.x_root - self._drag_data["x"]
        ny = event.y_root - self._drag_data["y"]
        self.geometry(f"+{nx}+{ny}")
        self._drag_data["moved"] = True

    def _on_drag_end(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._drag_data["moved"]:
            self._save_position()

    def _toggle_lock(self, event=None) -> None:  # type: ignore[no-untyped-def]
        self._locked = not self._locked
        # Visual cue: change border color when locked.
        self.configure(fg_color=_C["ok"] if self._locked else _C["purple"])

    # ── Auto-fade ─────────────────────────────────────────────────

    def _set_alpha(self, alpha: float) -> None:
        """Set window translucency; clamped + cached so we don't pound
        Tk with redundant updates."""
        a = max(0.05, min(1.0, float(alpha)))
        if abs(a - self._current_alpha) < 0.01:
            return
        try:
            self.attributes("-alpha", a)
            self._current_alpha = a
        except Exception:  # noqa: BLE001
            pass

    def _cursor_near(self) -> bool:
        """True if the global mouse cursor is within FADE_PROXIMITY_PX
        of the overlay's bounds. Uses winfo_pointer{x,y} which works
        even though our window is overrideredirect."""
        try:
            mx = self.winfo_pointerx()
            my = self.winfo_pointery()
            x = self.winfo_x()
            y = self.winfo_y()
            w = self.winfo_width() or _OVERLAY_W
            h = self.winfo_height() or _OVERLAY_H
        except Exception:  # noqa: BLE001
            return False
        # Distance to nearest edge of the rect.
        dx = max(x - mx, 0, mx - (x + w))
        dy = max(y - my, 0, my - (y + h))
        return (dx * dx + dy * dy) <= (_FADE_PROXIMITY_PX * _FADE_PROXIMITY_PX)

    def _poll_proximity(self) -> None:
        """Tick: restore alpha when cursor near, fade out after idle.
        Also tracks the foreground HWND so a subsequent click can
        restore focus to the right window before firing Ctrl+A+Ctrl+C.
        """
        now_ms = int(time.time() * 1000)
        if self._cursor_near():
            self._last_proximity_ms = now_ms
            self._set_alpha(_FADE_ACTIVE_ALPHA)
        elif now_ms - self._last_proximity_ms >= _FADE_DELAY_MS:
            self._set_alpha(_FADE_IDLE_ALPHA)

        # Track foreground HWND. Skip our own root + any picker we
        # might own so we don't save the overlay/picker as the
        # "external" window the user was typing in.
        if _WIN32_OK:
            try:
                fg = int(_user32.GetForegroundWindow())
                # GA_ROOT = 2; resolve our Toplevel root because
                # winfo_id() returns the inner Tk drawable handle.
                my_root = int(_user32.GetAncestor(int(self.winfo_id()), 2))
                if fg and fg != my_root:
                    self._last_external_hwnd = fg
            except Exception as e:
                # Log but keep the poll alive — repeated user32
                # failures point to a broken environment (DLL unloaded
                # at session shutdown, etc.). Stale _last_external_hwnd
                # would otherwise silently misroute Ctrl+A+Ctrl+C.
                logger.debug("Foreground-HWND poll failed: %s", e)

        # Always reschedule — cancellation happens on widget destroy
        # via Tk's own cleanup of pending after() callbacks.
        try:
            self._fade_job = self.after(
                _FOREGROUND_POLL_MS, self._poll_proximity,
            )
        except tk.TclError:
            self._fade_job = None

    # ── Click pipeline ────────────────────────────────────────────

    def _on_click(self) -> None:
        # Don't fire if we just finished dragging the window
        if self._drag_data.get("moved"):
            self._drag_data["moved"] = False
            return

        if pyautogui is None or pyperclip is None:
            logger.warning("Overlay click requires pyautogui + pyperclip")
            return

        # Snapshot the most-recent external foreground HWND on the Tk
        # thread BEFORE the worker thread starts — by the time the worker
        # runs Ctrl+A+Ctrl+C, the overlay has stolen focus and
        # GetForegroundWindow() would return our own window.
        target_hwnd = self._last_external_hwnd

        # Run capture+improve in a thread so the UI doesn't freeze.
        threading.Thread(
            target=self._capture_and_improve,
            args=(target_hwnd,),
            daemon=True,
        ).start()

    def _capture_and_improve(self, target_hwnd: int = 0) -> None:
        # Send Ctrl+A then Ctrl+C to focused window. Brief pause for the
        # OS to finish selection before reading clipboard.
        try:
            # Save current clipboard so we can restore if capture fails.
            saved = ""
            try:
                saved = pyperclip.paste()
            except Exception:
                pass

            # Restore foreground to the window the user was actually
            # typing in. Without this the macro hits the overlay (which
            # has nothing selectable) → empty clipboard → silent abort.
            if _WIN32_OK and target_hwnd:
                try:
                    if _user32.IsWindow(target_hwnd):
                        _user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
                        _user32.SetForegroundWindow(target_hwnd)
                        time.sleep(0.08)  # let OS process focus change
                except Exception as e:
                    logger.debug("Foreground restore failed: %s", e)

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.08)

            captured = ""
            try:
                captured = pyperclip.paste()
            except Exception as e:
                logger.warning("Clipboard read failed: %s", e)

            captured = (captured or "").strip()
            if not captured:
                logger.info("Overlay capture: empty clipboard, aborting")
                return

            # Show project picker on the main thread.
            self.after(0, lambda c=captured, s=saved: self._show_picker(c, s))
        except Exception as e:
            logger.exception("Overlay capture failed: %s", e)

    def _show_picker(self, captured: str, saved_clipboard: str) -> None:
        """Render a tiny project picker popup near the overlay."""
        picker = ctk.CTkToplevel(self)
        picker.overrideredirect(True)
        picker.attributes("-topmost", True)
        picker.configure(fg_color=_C["card"])
        # Group picker with the overlay (not the hidden CTk root) so
        # raise/focus calls don't bubble up the parent chain and
        # surface the withdrawn root window as a maximized empty
        # "CTk" frame.
        try:
            picker.transient(self)
        except Exception:
            pass

        # Position below the overlay, clamped to screen bounds. Without
        # clamping, an overlay near the screen edge produces a picker
        # that renders partially or fully off-screen — the user sees the
        # title only and can't pick a project. We prefer below-overlay,
        # flip above when below would overflow, and clamp horizontally.
        ox = self.winfo_x()
        oy = self.winfo_y()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080  # safe fallback

        # Vertical placement.
        y_below = oy + _OVERLAY_H + _PICKER_GAP
        if y_below + _PICKER_H + _SCREEN_MARGIN <= sh:
            y = y_below
        else:
            y_above = oy - _PICKER_H - _PICKER_GAP
            y = max(_SCREEN_MARGIN, y_above)
            # If even above overflows (tiny screens), final clamp.
            y = min(y, sh - _PICKER_H - _SCREEN_MARGIN)

        # Horizontal placement: left-aligned with overlay, then clamp.
        x = ox
        x = min(x, sw - _PICKER_W - _SCREEN_MARGIN)
        x = max(_SCREEN_MARGIN, x)

        picker.geometry(f"{_PICKER_W}x{_PICKER_H}+{x}+{y}")

        # Dismiss on Escape and on click-outside so the picker doesn't
        # stick around when the user clicks the underlying GUI or
        # another window. Without these binds the borderless+topmost
        # picker is un-closable except via its own Cancel button.
        def _safe_destroy() -> None:
            try:
                picker.destroy()
            except Exception:
                pass

        def _on_focus_out(_evt=None) -> None:
            # Defer the focus check — when the user clicks an internal
            # CTkButton, focus shifts from Toplevel to the button and
            # FocusOut fires; we don't want to dismiss in that case.
            def _check() -> None:
                try:
                    focused = picker.focus_displayof()
                except Exception:
                    focused = None
                if focused is None:
                    _safe_destroy()
                    return
                # Walk up the widget tree to see if the focused widget
                # is a descendant of the picker. If yes, focus is still
                # inside us — keep the picker open.
                w = focused
                while w is not None:
                    if w is picker:
                        return
                    try:
                        w = w.master
                    except Exception:
                        break
                _safe_destroy()
            picker.after(120, _check)

        picker.bind("<Escape>", lambda _e: _safe_destroy())
        picker.bind("<FocusOut>", _on_focus_out)
        # Use focus_set (soft) instead of focus_force (hard) — the
        # latter walks up the Tk parent chain on Windows and can
        # un-withdraw the hidden root window as a side effect. lift()
        # raises Z-order of just the picker.
        picker.after(50, lambda: (picker.focus_set(), picker.lift()))

        ctk.CTkLabel(
            picker, text="Pick project for context:",
            font=("Segoe UI", 11, "bold"), text_color=_C["fg2"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        scroll = ctk.CTkScrollableFrame(picker, fg_color=_C["bg"], height=340)
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        # Loading placeholder. /projects can take several seconds the
        # first time (slug-walker filesystem scan) — previously this
        # ran synchronously with a 2s timeout, producing an empty
        # picker on cold cache. Now we render the picker immediately
        # and stream the list in via after(0, ...) once the HTTP
        # request returns. User can still hit "None — typo fix only"
        # or Cancel without waiting.
        loading_lbl = ctk.CTkLabel(
            scroll, text="Loading projects...",
            font=("Segoe UI", 10), text_color=_C["fg3"],
        )
        loading_lbl.pack(anchor="w", padx=6, pady=10)

        def _pick(path: str) -> None:
            picker.destroy()
            threading.Thread(
                target=self._post_improve,
                args=(captured, path, saved_clipboard),
                daemon=True,
            ).start()

        def _populate(projects: list[dict], error_reason: str = "") -> None:
            try:
                if not picker.winfo_exists():
                    return
            except Exception as e:
                logger.debug("picker winfo_exists check failed: %s", e)
                return
            try:
                loading_lbl.destroy()
            except Exception as e:
                # Normal during picker teardown race; logged at debug
                # so it isn't silent if it ever recurs at scale.
                logger.debug("loading_lbl destroy failed: %s", e)
            # Wipe any previous result rows so a retry doesn't stack
            # on top of an empty-state label.
            for child in scroll.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            if error_reason:
                ctk.CTkLabel(
                    scroll, text=f"Couldn't load projects:\n{error_reason}",
                    font=("Segoe UI", 10), text_color=_C["err"],
                    wraplength=280, justify="left",
                ).pack(anchor="w", padx=6, pady=(10, 4))
                ctk.CTkButton(
                    scroll, text="Retry",
                    font=("Segoe UI", 10, "bold"),
                    fg_color=_C["accent"], hover_color="#1a8ae8",
                    text_color="#fff", height=28,
                    command=lambda: threading.Thread(
                        target=_fetch, daemon=True, name="ts_picker_retry",
                    ).start(),
                ).pack(anchor="w", padx=6, pady=(0, 8))
                return
            if not projects:
                ctk.CTkLabel(
                    scroll,
                    text="(no projects yet)\nRun Bootstrap on a project first.",
                    font=("Segoe UI", 10), text_color=_C["fg3"],
                    wraplength=280, justify="left",
                ).pack(anchor="w", padx=6, pady=10)
                return
            for proj in projects:
                ptitle = proj.get("name", proj.get("slug", "?"))
                ppath = proj.get("path", "")
                label = f"{ptitle}\n{ppath or '(path unrecoverable)'}"
                b = ctk.CTkButton(
                    scroll, text=label, anchor="w",
                    font=("Segoe UI", 10),
                    fg_color=_C["bg"], hover_color=_C["border"],
                    text_color=_C["fg"],
                    state="normal" if ppath else "disabled",
                    command=lambda p=ppath: _pick(p),
                )
                b.pack(fill="x", pady=2)

        # None + Cancel — packed BEFORE the projects fetch so user can
        # always dismiss while the list loads. Bottom row of picker.
        bottom = ctk.CTkFrame(picker, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(
            bottom, text="None — typo fix only",
            font=("Segoe UI", 10),
            fg_color=_C["ok"], hover_color="#0e6e0e",
            command=lambda: _pick(""),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bottom, text="Cancel",
            font=("Segoe UI", 10),
            fg_color=_C["bg"], text_color=_C["fg2"],
            command=picker.destroy,
        ).pack(side="left")

        # Background fetch — timeout generous since slug-walker can
        # take several seconds on cold cache. Result lands on Tk main
        # thread via picker.after(0, ...). Captures error reason so the
        # picker can show why instead of a generic "(no projects yet)"
        # that hides timeouts and 5xx behind the empty state.
        def _fetch() -> None:
            projs: list[dict] = []
            error_reason = ""
            # Reset to loading state on retry — picker may already show
            # an error label from a prior failed fetch.
            try:
                picker.after(0, lambda: (
                    [c.destroy() for c in scroll.winfo_children()],
                    ctk.CTkLabel(
                        scroll, text="Loading projects...",
                        font=("Segoe UI", 10), text_color=_C["fg3"],
                    ).pack(anchor="w", padx=6, pady=10),
                ))
            except Exception as e:
                logger.debug("picker.after loading-state schedule failed: %s", e)
            try:
                r = urllib.request.urlopen(
                    f"http://127.0.0.1:{self._prefs.http_port}/projects",
                    timeout=8,
                )
                data = json.loads(r.read())
                projs = data.get("projects", []) or []
            except Exception as e:
                error_reason = type(e).__name__ + (f": {e}" if str(e) else "")
                logger.warning("/projects fetch failed: %s", error_reason)
            try:
                picker.after(0, _populate, projs, error_reason)
            except Exception as e:
                # picker.after() can raise TclError when the picker
                # was destroyed before the fetch returned. Logged so
                # any non-race TclError (interpreter shutdown, etc.)
                # is observable.
                logger.debug("picker.after schedule failed: %s", e)

        threading.Thread(target=_fetch, daemon=True,
                         name="ts_picker_fetch").start()

    def _post_improve(
        self, prompt: str, project_path: str, saved_clipboard: str,
    ) -> None:
        """POST to /improve. The GUI picks up the result via pending file.

        We deliberately do NOT call AllowSetForegroundWindow here even
        though the overlay process is foreground-eligible. The grant is
        time-limited by Windows (expires on next user input, ~1s), and
        urlopen + the GUI's pending-file poll loop can take longer than
        that. The tray's HTTP handler does the grant right before
        spawning/signaling the GUI in http_server.py — that's the right
        moment.
        """
        error: str = ""
        try:
            body = json.dumps({
                "prompt": prompt, "project_path": project_path,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{self._prefs.http_port}/improve",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                _ = r.read()
        except Exception as e:
            error = type(e).__name__ + (f": {e}" if str(e) else "")
            logger.warning("Overlay /improve POST failed: %s", error)
        finally:
            # Restore original clipboard if any (best-effort).
            if pyperclip is not None and saved_clipboard:
                try:
                    pyperclip.copy(saved_clipboard)
                except Exception:
                    pass
        # Schedule the user-visible error on the Tk main thread. Without
        # this the overlay silently swallows network failures and the
        # user thinks Improve is broken.
        if error:
            try:
                self.after(0, lambda msg=error: self._show_error_toast(msg))
            except Exception as e:
                logger.debug("error toast schedule failed: %s", e)

    def _show_error_toast(self, msg: str) -> None:
        """Tiny self-dismissing CTkToplevel near the overlay reporting failure.

        Plain Toplevel rather than a CTkLabel `place`d on the overlay so it
        survives even if the overlay is faded to 30% idle alpha — the user
        needs to see this regardless of overlay opacity.
        """
        try:
            tw = ctk.CTkToplevel(self)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            ox, oy = self.winfo_x(), self.winfo_y()
            tw.geometry(f"260x60+{ox - 60}+{oy + _OVERLAY_H + 6}")
            tw.configure(fg_color=_C["err"])
            ctk.CTkLabel(
                tw,
                text=f"Improve failed\n{msg[:140]}",
                font=("Segoe UI", 10, "bold"),
                text_color="#ffffff",
                wraplength=240,
                justify="left",
            ).pack(fill="both", expand=True, padx=8, pady=6)
            tw.after(4000, lambda: self._safe_destroy(tw))
        except Exception as e:
            logger.debug("error toast build failed: %s", e)

    @staticmethod
    def _safe_destroy(widget) -> None:
        try:
            widget.destroy()
        except Exception:
            pass


def open_overlay(parent: ctk.CTk) -> OverlayButton:
    """Construct + return an overlay attached to `parent`."""
    return OverlayButton(parent)


# ── Standalone process entry point ──────────────────────────────────

_OVERLAY_INSTANCE_NAME = "ClaudeTokenSaverOverlay"


def _install_overlay_file_logger() -> None:
    """Mirror overlay's logger to ~/.claude/session-data/<date>/exe_Overlay.log.

    Frozen exe has no console, so warnings vanished into the void. The file
    handler is best-effort: any failure here is silent (logged at debug
    via the existing logger config) since we don't want logging setup to
    crash the overlay process.
    """
    try:
        from datetime import date
        log_dir = Path.home() / ".claude" / "session-data" / date.today().isoformat()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "exe_Overlay.log"
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
        ))
        logging.getLogger().addHandler(fh)
        logger.info("overlay logger attached to %s", log_path)
    except Exception as e:
        logger.debug("overlay file logger install failed: %s", e)


def main() -> int:
    """Run overlay as its own process with a hidden parent Tk root.

    Tray spawns this as a detached subprocess when prefs.show_overlay is
    True, so the overlay is independent of the GUI window's lifetime.
    Single-instance enforced via shared lock (re-launching is a no-op).
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _install_overlay_file_logger()

    # Best-effort cleanup of any stale raise-flag left behind by a
    # previously-crashed overlay instance — otherwise we'd "raise" on
    # boot for a launch attempt that happened long before we started.
    from .single_instance import _flag_path
    try:
        _flag_path(_OVERLAY_INSTANCE_NAME).unlink(missing_ok=True)
    except OSError as e:
        logger.debug("stale overlay raise-flag cleanup failed: %s", e)

    from .single_instance import acquire_or_exit
    _lock = acquire_or_exit(_OVERLAY_INSTANCE_NAME)  # noqa: F841

    # Hidden root window — only exists to host the Toplevel overlay.
    # Defense-in-depth so the root stays invisible even if some Tk
    # action (focus_force on a child, etc.) un-withdraws it:
    #   - tiny 1x1 geometry positioned off the visible area
    #   - alpha 0 so it's transparent if it does surface
    #   - tool-window flag suppresses the taskbar entry
    #   - finally withdraw() to hide it normally
    root = ctk.CTk()
    try:
        root.geometry("1x1+-32000+-32000")
        root.attributes("-alpha", 0.0)
        root.attributes("-toolwindow", True)
    except Exception:
        pass
    root.withdraw()

    button = OverlayButton(root)

    # Raise-flag poller — consumes ~/.claude/ClaudeTokenSaverOverlay_raise.flag
    # written by `acquire_or_exit` when a duplicate `--overlay` launch is
    # rejected. On flag, lift the floating button to the top and briefly
    # toggle topmost so the user sees it move to foreground.
    from .single_instance import poll_bring_to_front_flag

    def _on_raise() -> None:
        try:
            button.lift()
            button.attributes("-topmost", True)
            # 200ms is enough for Windows to honor the topmost re-assert,
            # short enough that the user perceives it as a single flash.
            button.after(200, lambda: button.attributes("-topmost", False))
        except Exception as e:
            logger.debug("overlay raise failed: %s", e)

    def _tick_raise() -> None:
        try:
            poll_bring_to_front_flag(_OVERLAY_INSTANCE_NAME, _on_raise)
        except Exception as e:
            logger.debug("overlay raise-flag poll failed: %s", e)
        try:
            root.after(1500, _tick_raise)
        except Exception as e:
            # TclError during teardown — loop ends naturally.
            logger.debug("overlay raise-flag reschedule failed: %s", e)

    root.after(1500, _tick_raise)

    root.mainloop()
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
