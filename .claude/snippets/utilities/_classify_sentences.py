# From: classifier/splitter.py:108
# Classify each sentence independently.

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
