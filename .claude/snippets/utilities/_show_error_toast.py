# From: claude_backend/overlay.py:717
# Tiny self-dismissing CTkToplevel near the overlay reporting failure.

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
