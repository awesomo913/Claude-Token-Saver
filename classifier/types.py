"""Shared data types for PromptRouter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskClassification:
    """Result of classifying a prompt."""
    complexity_score: float          # 0.0 (trivial) to 1.0 (expert-level)
    task_types: list[str]            # detected task categories
    domains: list[str]               # detected technical domains
    routing: str                     # "free", "claude", "split"
    confidence: float                # 0.0–1.0
    reasoning: str                   # human-readable explanation
    estimated_free_pct: float        # 0.0–1.0 how much can go to free models
    signal_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubTask:
    """A single decomposed piece of a prompt."""
    text: str
    routing: str                     # "free" or "claude"
    task_type: str                   # from classification
    estimated_tokens: int = 0


@dataclass
class RoutingResult:
    """Complete routing output from the splitter."""
    original_prompt: str
    subtasks: list[SubTask]
    free_prompt: str                 # assembled prompt for free models
    claude_prompt: str               # trimmed prompt for Claude
    free_token_estimate: int = 0
    claude_token_estimate: int = 0
    savings_pct: float = 0.0


@dataclass
class ModelInfo:
    """Description of an available model."""
    id: str
    name: str
    context_length: int = 0
    is_free: bool = False
    provider: str = ""


@dataclass
class BackendResponse:
    """Response from any AI backend."""
    text: str
    model: str
    backend: str
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_sec: float = 0.0
    error: str = ""


@dataclass
class SavingsEvent:
    """Single routing event for the tracker."""
    timestamp: str
    original_tokens: int
    free_tokens_sent: int
    claude_tokens_needed: int
    tokens_saved: int
    cost_saved_usd: float
    backend_used: str
    model_used: str
    routing_decision: str
    task_types: list[str]
    elapsed_sec: float = 0.0
    prompt_preview: str = ""  # first 200 chars of original prompt


@dataclass
class SavingsSummary:
    """Aggregate savings stats."""
    total_prompts: int = 0
    tokens_sent_to_free: int = 0
    tokens_sent_to_claude: int = 0
    tokens_avoided: int = 0
    estimated_cost_saved: float = 0.0
    avg_free_pct: float = 0.0
    by_backend: dict[str, int] = field(default_factory=dict)
    by_task_type: dict[str, int] = field(default_factory=dict)
