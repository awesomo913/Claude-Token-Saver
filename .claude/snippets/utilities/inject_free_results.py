# From: smart_router.py:63
# Replace the {free_model_results} placeholder with actual output.

    @staticmethod
    def inject_free_results(claude_prompt: str, free_response: str) -> str:
        """Replace the {free_model_results} placeholder with actual output."""
        if "{free_model_results}" in claude_prompt:
            return claude_prompt.replace("{free_model_results}", free_response)
        return (
            "The following work was already completed by a free model:\n\n"
            f"--- FREE MODEL OUTPUT ---\n{free_response}\n"
            "--- END FREE MODEL OUTPUT ---\n\n"
            "Now handle the remaining work:\n\n" + claude_prompt
        )
