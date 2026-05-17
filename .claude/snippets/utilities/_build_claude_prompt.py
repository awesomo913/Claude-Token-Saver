# From: classifier/splitter.py:151
# Assemble the Claude prompt, including a slot for free model results.

    @staticmethod
    def _build_claude_prompt(subtasks: list[SubTask], original: str) -> str:
        """Assemble the Claude prompt, including a slot for free model results."""
        claude_parts = [st.text for st in subtasks if st.routing == "claude"]
        if not claude_parts:
            return ""

        free_parts = [st.text for st in subtasks if st.routing == "free"]
        header = ""
        if free_parts:
            header = (
                "NOTE: The following parts of this task were already completed by a "
                "free model. Their output is provided below for context.\n\n"
                "--- FREE MODEL RESULTS ---\n"
                "{free_model_results}\n"
                "--- END FREE MODEL RESULTS ---\n\n"
                "Please handle the remaining work:\n\n"
            )

        return header + "\n\n".join(claude_parts)
