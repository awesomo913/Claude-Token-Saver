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


class OverlayButton(ctk.CTkToplevel):
    """Always-on-top floating button. Owned by the GUI app's lifetime."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self._parent = parent
        self._prefs = Prefs.load()
        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._locked = False

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

    # ── Click pipeline ────────────────────────────────────────────

    def _on_click(self) -> None:
        # Don't fire if we just finished dragging the window
        if self._drag_data.get("moved"):
            self._drag_data["moved"] = False
            return

        if pyautogui is None or pyperclip is None:
            logger.warning("Overlay click requires pyautogui + pyperclip")
            return

        # Run capture+improve in a thread so the UI doesn't freeze.
        threading.Thread(target=self._capture_and_improve, daemon=True).start()

    def _capture_and_improve(self) -> None:
        # Send Ctrl+A then Ctrl+C to focused window. Brief pause for the
        # OS to finish selection before reading clipboard.
        try:
            # Save current clipboard so we can restore if capture fails.
            saved = ""
            try:
                saved = pyperclip.paste()
            except Exception:
                pass

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

        # Position below the overlay
        x = self.winfo_x()
        y = self.winfo_y() + _OVERLAY_H + 6
        picker.geometry(f"320x300+{x}+{y}")

        ctk.CTkLabel(
            picker, text="Pick project for context:",
            font=("Segoe UI", 11, "bold"), text_color=_C["fg2"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Fetch projects via HTTP
        projects: list[dict] = []
        try:
            r = urllib.request.urlopen(
                f"http://127.0.0.1:{self._prefs.http_port}/projects", timeout=2,
            )
            data = json.loads(r.read())
            projects = data.get("projects", [])
        except Exception as e:
            logger.warning("/projects fetch failed: %s", e)

        scroll = ctk.CTkScrollableFrame(picker, fg_color=_C["bg"], height=180)
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        def _pick(path: str) -> None:
            picker.destroy()
            threading.Thread(
                target=self._post_improve,
                args=(captured, path, saved_clipboard),
                daemon=True,
            ).start()

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

        # None + Cancel
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

    def _post_improve(
        self, prompt: str, project_path: str, saved_clipboard: str,
    ) -> None:
        """POST to /improve. The GUI picks up the result via pending file."""
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
            logger.warning("Overlay /improve POST failed: %s", e)
        finally:
            # Restore original clipboard if any (best-effort).
            if pyperclip is not None and saved_clipboard:
                try:
                    pyperclip.copy(saved_clipboard)
                except Exception:
                    pass


def open_overlay(parent: ctk.CTk) -> OverlayButton:
    """Construct + return an overlay attached to `parent`."""
    return OverlayButton(parent)


# ── Standalone process entry point ──────────────────────────────────

_OVERLAY_INSTANCE_NAME = "ClaudeTokenSaverOverlay"


def main() -> int:
    """Run overlay as its own process with a hidden parent Tk root.

    Tray spawns this as a detached subprocess when prefs.show_overlay is
    True, so the overlay is independent of the GUI window's lifetime.
    Single-instance enforced via shared lock (re-launching is a no-op).
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    from .single_instance import acquire_or_exit
    _lock = acquire_or_exit(_OVERLAY_INSTANCE_NAME)  # noqa: F841

    # Hidden root window — only exists to host the Toplevel overlay.
    root = ctk.CTk()
    root.withdraw()  # Hide the root; only the overlay Toplevel is visible.

    OverlayButton(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
