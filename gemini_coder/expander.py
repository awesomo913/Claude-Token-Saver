"""Expander - task expansion for Gemini Coder."""

import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class ExpansionEngine:
    """Engine for expanding simple tasks into detailed prompts."""

    def __init__(self, client, depth_limit: int = 3) -> None:
        self._client = client
        self._depth_limit = depth_limit

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

    @property
    def depth_limit(self) -> int:
        return self._depth_limit

    @depth_limit.setter
    def depth_limit(self, value: int) -> None:
        self._depth_limit = max(1, min(value, 10))
