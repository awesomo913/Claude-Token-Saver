# From: gemini_coder/expander.py:16
# Expand a simple task description into a detailed prompt.

    def expand_task(
        self,
        task: str,
        on_progress: Optional[Callable] = None,
    ) -> str:
        """Expand a simple task description into a detailed prompt."""
        if on_progress:
            on_progress(f"Expanding task: {task[:50]}...")
        
        expansion_prompt = f"""You are a task architect. Take this simple task and expand it 
into a detailed, production-ready specification.

Task: {task}

Provide:
1. A clear problem statement
2. Key requirements and constraints
3. Suggested architecture/approach
4. Edge cases to handle
5. Success criteria

Be specific and actionable. This will be used to generate code."""

        try:
            result = self._client.generate(prompt=expansion_prompt)
            if on_progress:
                on_progress("Task expanded successfully")
            return result
        except Exception as e:
            logger.error("Expansion failed: %s", e)
            return task
