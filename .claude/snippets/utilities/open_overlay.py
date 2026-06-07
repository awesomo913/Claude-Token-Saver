# From: claude_backend/overlay.py:751
# Construct + return an overlay attached to `parent`.

def open_overlay(parent: ctk.CTk) -> OverlayButton:
    """Construct + return an overlay attached to `parent`."""
    return OverlayButton(parent)
