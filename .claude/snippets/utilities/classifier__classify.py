# From: classifier/classifier.py:37
# Analyze a prompt and return classification with routing decision.

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
