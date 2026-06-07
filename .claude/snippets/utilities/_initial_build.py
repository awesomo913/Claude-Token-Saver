# From: NeoAutocoder/core_loop.py:139
# Initial codebase generation.

    def _initial_build(self, session: Session, task: str) -> str:
        """Initial codebase generation."""
        prompt = f"""You are an expert Python developer.
Create a COMPLETE, production-ready implementation for the following task:

TASK: {task}

Requirements:
- CODE FIRST: Output the complete working codebase in a single ```python fenced block.
- Make it SOLID, well-documented, with type hints where appropriate.
- Include comprehensive docstrings and comments.
- Follow PEP 8.
- Any review or explanation comes AFTER the code block.

Begin."""
        
        response = self.provider_chain.generate(prompt)
        code = extract_code(response, "initial")
        if not code or len(code) < 1000:
            code = "# Initial placeholder - implement the task below\n" + task
        return code
