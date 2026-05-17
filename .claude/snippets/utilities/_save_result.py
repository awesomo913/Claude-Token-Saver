# From: broadcast.py:303
# Save an iteration's actual result to Downloads.

    def _save_result(self, session, task: str, iteration: int,
                     focus: str, result: str, start_time: float) -> None:
        """Save an iteration's actual result to Downloads."""
        try:
            title = f"{task[:40]}_iter{iteration}_{focus.replace(' ', '_')}"
            path = save_task_output(
                title=title,
                output=result,
                ai_name=session.ai_profile.name,
                corner=session.corner,
                elapsed_seconds=time.time() - start_time,
                iterations=iteration,
            )
            if path and self._on_status:
                self._on_status(f"Saved: {path.name}")
        except Exception as e:
            logger.warning("Auto-save failed for %s: %s", session.display_name, e)
