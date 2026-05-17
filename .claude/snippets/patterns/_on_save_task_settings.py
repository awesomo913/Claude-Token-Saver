# From: ui/app_web.py:1314

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
