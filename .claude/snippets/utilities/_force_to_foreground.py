# From: claude_backend/gui.py:803
# Robustly surface the GUI window. Combines Tk's lift+focus_force

    def _force_to_foreground(self) -> None:
        """Robustly surface the GUI window. Combines Tk's lift+focus_force
        with Win32 ShowWindow(SW_RESTORE) + SetForegroundWindow + a
        keybd_event ALT-tickle to defeat LockSetForegroundWindow.

        Plain `lift()` + `focus_force()` often only blinks the taskbar
        when this process isn't already foreground — Windows' policy
        prevents background processes from stealing focus. The ALT
        keybd_event simulates a no-op user input which fools the policy
        into treating us as foreground-eligible (documented Win32
        workaround used by PowerToys, Slack, etc.). Pairs with
        `AllowSetForegroundWindow(ASFW_ANY)` called by the overlay /
        tray process before the pending file is written.
        """
        # Tk path first — covers non-Win32 and is harmless when the
        # window is already up and focused.
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception as e:
            logger.debug("Tk raise failed: %s", e)

        win32_ok = False
        if sys.platform == "win32":
            try:
                import ctypes
                u32 = ctypes.windll.user32
                # Resolve our top-level HWND (winfo_id is the inner
                # drawable handle). GA_ROOT = 2 walks up to the
                # owning Toplevel.
                hwnd = int(u32.GetAncestor(int(self.winfo_id()), 2))
                if hwnd and u32.IsWindow(hwnd):
                    # Decide window-state command BEFORE the tickle so
                    # we don't disturb a maximized window. SW_RESTORE
                    # un-maximizes — only OK when the window is
                    # actually minimized. SW_SHOW is a safe no-op for
                    # already-visible windows that just nudges Z-order.
                    is_min = bool(u32.IsIconic(hwnd))
                    needs_raise = is_min or not u32.IsWindowVisible(hwnd)

                    if needs_raise:
                        # ALT-tickle: press+release VK_MENU so Windows
                        # treats us as foreground-eligible. Skipped when
                        # the window is already visible+normal because
                        # the tickle leaks to the focused app (Claude,
                        # Chrome, etc.) as a phantom ALT keystroke.
                        VK_MENU = 0x12
                        KEYEVENTF_KEYUP = 0x0002
                        u32.keybd_event(VK_MENU, 0, 0, 0)
                        u32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

                    # SW_RESTORE = 9 (un-minimizes — DESTROYS maximize),
                    # SW_SHOW = 5 (just makes visible, preserves state).
                    u32.ShowWindow(hwnd, 9 if is_min else 5)
                    if u32.SetForegroundWindow(hwnd):
                        u32.BringWindowToTop(hwnd)
                        win32_ok = True
                    else:
                        # SetForegroundWindow returning 0 usually means
                        # the AllowSetForegroundWindow grant has
                        # expired or never propagated to this process.
                        # Log so a recurring foreground-grant problem
                        # is observable instead of just falling
                        # through to the topmost-flash silently.
                        logger.info(
                            "SetForegroundWindow refused (grant expired?) — "
                            "falling back to topmost-flash",
                        )
            except Exception as e:
                logger.debug("Win32 raise failed: %s", e)

        # Topmost flash only if the Win32 path did NOT succeed —
        # otherwise the window would briefly pin above other apps for
        # 200ms even on a clean raise, which is visually disruptive.
        if not win32_ok:
            try:
                self.attributes("-topmost", True)
                self.after(200, lambda: self.attributes("-topmost", False))
            except Exception as e:
                logger.debug("topmost-flash fallback failed: %s", e)
