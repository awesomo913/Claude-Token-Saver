"""Task splitter — decomposes a mixed prompt into free-model and Claude subtasks."""

from __future__ import annotations

import re
from .types import RoutingResult, SubTask, TaskClassification
from .classifier import PromptClassifier


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)


class TaskSplitter:
    """Split a prompt into free-model and Claude subtasks."""

    def __init__(self, classifier: PromptClassifier) -> None:
        self._classifier = classifier

    def split(
        self, prompt: str, classification: TaskClassification
    ) -> RoutingResult:
        """Decompose prompt into routed subtasks and build two output prompts."""

        if classification.routing == "free":
            return self._all_free(prompt)
        if classification.routing == "claude":
            return self._all_claude(prompt)

        # Split mode
        sentences = self._split_sentences(prompt)
        subtasks = self._classify_sentences(sentences)
        subtasks = self._merge_consecutive(subtasks)

        free_prompt = self._build_free_prompt(subtasks)
        claude_prompt = self._build_claude_prompt(subtasks, prompt)

        free_tokens = _estimate_tokens(free_prompt)
        claude_tokens = _estimate_tokens(claude_prompt)
        original_tokens = _estimate_tokens(prompt)
        savings = max(0.0, 1.0 - (claude_tokens / max(1, original_tokens)))

        return RoutingResult(
            original_prompt=prompt,
            subtasks=subtasks,
            free_prompt=free_prompt,
            claude_prompt=claude_prompt,
            free_token_estimate=free_tokens,
            claude_token_estimate=claude_tokens,
            savings_pct=round(savings, 3),
        )

    def _all_free(self, prompt: str) -> RoutingResult:
        tokens = _estimate_tokens(prompt)
        return RoutingResult(
            original_prompt=prompt,
            subtasks=[SubTask(text=prompt, routing="free", task_type="all",
                              estimated_tokens=tokens)],
            free_prompt=prompt,
            claude_prompt="",
            free_token_estimate=tokens,
            claude_token_estimate=0,
            savings_pct=1.0,
        )

    def _all_claude(self, prompt: str) -> RoutingResult:
        tokens = _estimate_tokens(prompt)
        return RoutingResult(
            original_prompt=prompt,
            subtasks=[SubTask(text=prompt, routing="claude", task_type="all",
                              estimated_tokens=tokens)],
            free_prompt="",
            claude_prompt=prompt,
            free_token_estimate=0,
            claude_token_estimate=tokens,
            savings_pct=0.0,
        )

    @staticmethod
    def _split_sentences(prompt: str) -> list[str]:
        """Split on sentence boundaries, preserving code blocks as single units."""
        # Extract code blocks first
        code_blocks: list[str] = []
        def _replace_code(m: re.Match) -> str:
            code_blocks.append(m.group(0))
            return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

        text = re.sub(r"```[\s\S]*?```", _replace_code, prompt)

        # Split on sentence endings
        raw = re.split(r"(?<=[.!?])\s+", text.strip())
        # Also split on newlines that look like list items or new thoughts
        expanded: list[str] = []
        for chunk in raw:
            parts = re.split(r"\n(?=[-*\d]\.?\s|\n)", chunk)
            expanded.extend(p.strip() for p in parts if p.strip())

        # Restore code blocks
        result: list[str] = []
        for s in expanded:
            for i, block in enumerate(code_blocks):
                s = s.replace(f"__CODE_BLOCK_{i}__", block)
            result.append(s)

        return result

    def _classify_sentences(self, sentences: list[str]) -> list[SubTask]:
        """Classify each sentence independently."""
        subtasks: list[SubTask] = []
        for s in sentences:
            cls = self._classifier.classify(s)
            routing = "free" if cls.routing in ("free", "split") and cls.complexity_score < 0.5 else "claude"
            task_type = cls.task_types[0] if cls.task_types else "general"
            subtasks.append(SubTask(
                text=s,
                routing=routing,
                task_type=task_type,
                estimated_tokens=_estimate_tokens(s),
            ))
        return subtasks

    @staticmethod
    def _merge_consecutive(subtasks: list[SubTask]) -> list[SubTask]:
        """Merge consecutive subtasks with the same routing to avoid fragmentation."""
        if not subtasks:
            return subtasks

        merged: list[SubTask] = [subtasks[0]]
        for st in subtasks[1:]:
            prev = merged[-1]
            if st.routing == prev.routing:
                merged[-1] = SubTask(
                    text=prev.text + " " + st.text,
                    routing=prev.routing,
                    task_type=prev.task_type,
                    estimated_tokens=prev.estimated_tokens + st.estimated_tokens,
                )
            else:
                merged.append(st)
        return merged

    @staticmethod
    def _build_free_prompt(subtasks: list[SubTask]) -> str:
        """Assemble the prompt for free models from free subtasks."""
        free_parts = [st.text for st in subtasks if st.routing == "free"]
        if not free_parts:
            return ""
        return "\n\n".join(free_parts)

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
