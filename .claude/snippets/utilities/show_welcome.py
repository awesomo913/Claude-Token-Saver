# From: claude_backend/welcome.py:316
# Open welcome window. Returns dialog instance (caller can grab focus etc).

def show_welcome(parent: ctk.CTk, prefs: Prefs,
                 on_install_callback: Optional[Callable[[], None]] = None) -> WelcomeDialog:
    """Open welcome window. Returns dialog instance (caller can grab focus etc)."""
    dlg = WelcomeDialog(parent, prefs, on_install_callback=on_install_callback)
    dlg.lift()
    dlg.focus_force()
    return dlg
