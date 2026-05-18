# From: gemini_coder/expander.py:48
# Generate a code generation prompt from task and context.

    def generate_code_prompt(
        self,
        task: str,
        context: str = "",
        output_format: str = "Code Only",
    ) -> str:
        """Generate a code generation prompt from task and context."""
        return f"""{context}

Task: {task}

Requirements:
- Write complete, production-ready code
- No placeholders or TODOs
- Include proper error handling
- Add helpful comments

Output format: {output_format}

Generate the code:"""
