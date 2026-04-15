"""Smart Router — classifies prompts and chains free models into Claude.

Uses the bundled classifier (pure stdlib, no deps) and orchestrates
the split: easy parts → Gemini/free via CDP, hard parts → Claude via CDP.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

SMART_ROUTER_AVAILABLE = False
_import_error = ""

try:
    from .classifier import PromptClassifier, TaskSplitter, TaskClassification, RoutingResult
    SMART_ROUTER_AVAILABLE = True
except ImportError as e:
    _import_error = str(e)
    logger.warning("Smart Router unavailable: %s", e)

# AI profiles considered "free" (no API cost / browser-based free tier)
FREE_PROFILES = {"Gemini", "OpenRouter", "ChatGPT", "Copilot",
                 "Ollama Web UI", "Ollama (Terminal)", "LM Studio"}
CLAUDE_PROFILES = {"Claude"}


class SmartRouter:
    """Classify prompts and route between free + Claude sessions."""

    def __init__(self) -> None:
        if not SMART_ROUTER_AVAILABLE:
            raise RuntimeError(f"classifier not importable: {_import_error}")
        self._classifier = PromptClassifier()
        self._splitter = TaskSplitter(self._classifier)

    def classify(self, prompt: str) -> "TaskClassification":
        """Score the prompt and decide routing."""
        return self._classifier.classify(prompt)

    def split(self, prompt: str, cls: "TaskClassification") -> "RoutingResult":
        """Break prompt into free_prompt + claude_prompt."""
        return self._splitter.split(prompt, cls)

    @staticmethod
    def find_free_session(sessions: list) -> Optional[Any]:
        """Pick the first session running a free AI profile."""
        for s in sessions:
            if s.ai_profile.name in FREE_PROFILES and s.is_configured:
                return s
        return None

    @staticmethod
    def find_claude_session(sessions: list) -> Optional[Any]:
        """Pick the first session running Claude."""
        for s in sessions:
            if s.ai_profile.name in CLAUDE_PROFILES and s.is_configured:
                return s
        return None

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
