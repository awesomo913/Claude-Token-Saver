# From: classifier/splitter.py:123
# Merge consecutive subtasks with the same routing to avoid fragmentation.

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
