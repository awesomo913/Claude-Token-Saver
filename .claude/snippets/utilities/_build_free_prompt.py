# From: classifier/splitter.py:143
# Assemble the prompt for free models from free subtasks.

    @staticmethod
    def _build_free_prompt(subtasks: list[SubTask]) -> str:
        """Assemble the prompt for free models from free subtasks."""
        free_parts = [st.text for st in subtasks if st.routing == "free"]
        if not free_parts:
            return ""
        return "\n\n".join(free_parts)
