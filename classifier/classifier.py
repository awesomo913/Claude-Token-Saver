"""Local prompt classifier — determines routing without any API calls.

Uses weighted keyword matching + structural heuristics to score complexity
and decide whether a prompt should go to free models, Claude, or be split.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from .types import TaskClassification

logger = logging.getLogger(__name__)

_DEFAULT_KEYWORDS = Path(__file__).parent / "data" / "keywords.json"


class PromptClassifier:
    """Classify prompts by complexity and route to free models or Claude."""

    def __init__(self, keywords_path: Path | None = None) -> None:
        path = keywords_path or _DEFAULT_KEYWORDS
        self._keywords = self._load_keywords(path)

    @staticmethod
    def _load_keywords(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load keywords from %s: %s", path, e)
            return {"free_signals": {}, "claude_signals": {}, "domain_modifiers": {}}

    def classify(self, prompt: str) -> TaskClassification:
        """Analyze a prompt and return classification with routing decision."""
        lower = prompt.lower()

        free_score, free_types = self._score_signals(lower, "free_signals")
        claude_score, claude_types = self._score_signals(lower, "claude_signals")
        domain_adj = self._domain_adjustment(lower)
        structural = self._structural_complexity(prompt)
        file_refs = self._count_file_references(prompt)
        has_code = self._has_code_blocks(prompt)

        # Combine into final complexity score (0.0–1.0)
        raw = (
            (claude_score * 0.35)
            - (free_score * 0.25)
            + (structural * 0.25)
            + (domain_adj * 0.15)
        )
        complexity = max(0.0, min(1.0, raw + 0.3))  # baseline 0.3, clamp 0–1

        # File references push toward Claude
        if file_refs >= 3:
            complexity = min(1.0, complexity + 0.15)

        # Code blocks add modest complexity
        if has_code:
            complexity = min(1.0, complexity + 0.05)

        # Routing decision
        all_types = free_types + claude_types
        if complexity <= 0.30 and not claude_types:
            routing = "free"
            est_free = 1.0
        elif free_types and claude_types:
            # Both signal types present → split regardless of score
            routing = "split"
            est_free = max(0.1, min(0.9, free_score / max(0.1, free_score + claude_score)))
        elif complexity > 0.70 or (claude_score > free_score * 2 and claude_types):
            routing = "claude"
            est_free = 0.0
        else:
            routing = "split"
            est_free = max(0.1, min(0.9, 1.0 - complexity))

        # Safety check: scan sentences for hidden Claude signals
        if routing == "free" and len(prompt) > 150:
            sentences = re.split(r"(?<=[.!?])\s+", prompt.strip())
            for s in sentences:
                _, ct = self._score_signals(s.lower(), "claude_signals")
                if ct:
                    routing = "split"
                    est_free = max(0.3, est_free - 0.3)
                    all_types = list(dict.fromkeys(all_types + ct))
                    break

        # Metadata extraction: URLs, error patterns, code languages
        meta = self._extract_metadata(prompt)
        if meta["url_count"] >= 3:
            complexity = min(1.0, complexity + 0.05)
        if meta["error_blocks"]:
            complexity = min(1.0, complexity + 0.15)
            if routing == "free":
                routing = "split"
                est_free = max(0.2, est_free - 0.4)
        if meta["code_languages"]:
            complexity = min(1.0, complexity + 0.05 * len(meta["code_languages"]))

        # Confidence based on signal strength
        total_signal = free_score + claude_score
        if total_signal > 0:
            confidence = min(1.0, total_signal / 5.0)
        else:
            confidence = 0.3  # low confidence when no signals matched

        reasoning = self._build_reasoning(
            free_types, claude_types, complexity, structural, file_refs
        )
        if meta["error_blocks"]:
            reasoning += " | Contains error/traceback blocks"

        return TaskClassification(
            complexity_score=round(complexity, 3),
            task_types=all_types,
            domains=self._detect_domains(lower),
            routing=routing,
            confidence=round(confidence, 3),
            reasoning=reasoning,
            estimated_free_pct=round(est_free, 3),
            signal_details={
                "free_score": round(free_score, 2),
                "claude_score": round(claude_score, 2),
                "structural": round(structural, 2),
                "domain_adj": round(domain_adj, 2),
                "file_refs": file_refs,
                "has_code": has_code,
            },
        )

    def _score_signals(
        self, text: str, signal_group: str
    ) -> tuple[float, list[str]]:
        """Score keyword matches for a signal group."""
        groups = self._keywords.get(signal_group, {})
        total = 0.0
        matched_types: list[str] = []

        for category, info in groups.items():
            keywords = info.get("keywords", [])
            weight = info.get("weight", 1.0)
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                total += weight * min(hits, 3)  # cap per-category contribution
                matched_types.append(category)

        return total, matched_types

    def _domain_adjustment(self, text: str) -> float:
        """Adjust score based on domain detection. Positive = toward Claude."""
        adj = 0.0
        for _domain, info in self._keywords.get("domain_modifiers", {}).items():
            keywords = info.get("keywords", [])
            if any(kw in text for kw in keywords):
                strength = info.get("strength", 0.1)
                if info.get("bias") == "claude":
                    adj += strength
                else:
                    adj -= strength
        return adj

    def _detect_domains(self, text: str) -> list[str]:
        """Return list of detected domain names."""
        domains: list[str] = []
        for domain, info in self._keywords.get("domain_modifiers", {}).items():
            if any(kw in text for kw in info.get("keywords", [])):
                domains.append(domain)
        return domains

    @staticmethod
    def _structural_complexity(prompt: str) -> float:
        """Heuristic scoring based on prompt structure (0.0–1.0)."""
        score = 0.0

        sentences = re.split(r"(?<=[.!?])\s+", prompt.strip())
        if len(sentences) > 8:
            score += 0.2

        word_count = len(prompt.split())
        if word_count > 300:
            score += 0.1

        # Conditional language
        conditionals = ["but", "however", "except when", "edge case", "unless",
                        "only if", "special case", "in some cases"]
        if any(c in prompt.lower() for c in conditionals):
            score += 0.15

        # Error / stack trace indicators
        error_signs = ["traceback", "error:", "exception", "at line", "failed with",
                       "stack trace", "segmentation fault", "panic:"]
        if any(e in prompt.lower() for e in error_signs):
            score += 0.3

        return min(1.0, score)

    @staticmethod
    def _count_file_references(prompt: str) -> int:
        """Count references to file paths in the prompt."""
        patterns = [
            r"\b\w+\.\w{1,4}\b",  # file.ext
            r"[/\\]\w+[/\\]",      # path separators
        ]
        files = set()
        for p in patterns:
            files.update(re.findall(p, prompt))
        # Filter out common false positives
        exts = {".py", ".js", ".ts", ".c", ".h", ".json", ".yaml", ".toml",
                ".md", ".html", ".css", ".txt", ".rs", ".go", ".java"}
        real_files = [f for f in files if any(f.endswith(e) for e in exts)]
        return len(real_files)

    @staticmethod
    def _has_code_blocks(prompt: str) -> bool:
        return "```" in prompt

    @staticmethod
    def _extract_metadata(prompt: str) -> dict:
        """Extract URLs, code languages, error patterns from prompt."""
        urls = re.findall(r"https?://\S+", prompt)
        # Code block languages: ```python, ```c, ```javascript etc.
        code_langs = re.findall(r"```(\w+)", prompt)
        # Error/traceback blocks
        error_patterns = [
            r"Traceback \(most recent call last\)",
            r"^\s*File \".*\", line \d+",
            r"FATAL|panic:|SIGSEGV|segmentation fault",
            r"^\s*at [\w.]+\([\w.]+:\d+\)",  # Java/JS stack frames
        ]
        error_blocks = any(
            re.search(p, prompt, re.MULTILINE | re.IGNORECASE)
            for p in error_patterns
        )
        return {
            "url_count": len(urls),
            "code_languages": list(set(code_langs)),
            "error_blocks": error_blocks,
        }

    @staticmethod
    def _build_reasoning(
        free_types: list[str],
        claude_types: list[str],
        complexity: float,
        structural: float,
        file_refs: int,
    ) -> str:
        parts: list[str] = []
        if free_types:
            parts.append(f"Free-model signals: {', '.join(free_types)}")
        if claude_types:
            parts.append(f"Claude signals: {', '.join(claude_types)}")
        parts.append(f"Complexity: {complexity:.2f}")
        if structural > 0.1:
            parts.append(f"Structural complexity: {structural:.2f}")
        if file_refs >= 2:
            parts.append(f"References {file_refs} files")
        return " | ".join(parts)
