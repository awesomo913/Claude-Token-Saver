# From: claude_backend/tray.py:195
# Tray right-click menu. Default item (single-click) opens GUI.

def build_menu() -> Menu:
    """Tray right-click menu. Default item (single-click) opens GUI."""
    return Menu(
        MenuItem("Open Token Saver GUI", _launch_gui, default=True),
        MenuItem("Summon Improve overlay", _summon_overlay_action),
        Menu.SEPARATOR,
        MenuItem("Run prep on current folder", _run_prep),
        MenuItem(lambda _: _status_label(), None, enabled=False),
        Menu.SEPARATOR,
        MenuItem(
            "Snooze",
            Menu(
                MenuItem("1 hour", lambda icon, _: _snooze_action(icon, 1)),
                MenuItem("4 hours", lambda icon, _: _snooze_action(icon, 4)),
                MenuItem("Until tomorrow", lambda icon, _: _snooze_action(icon, 12)),
                MenuItem("Resume reminders", _unsnooze_action),
            ),
        ),
        Menu.SEPARATOR,
        MenuItem("Quit", _quit_action),
    )
