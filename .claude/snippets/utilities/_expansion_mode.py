# From: NeoAutocoder/core_loop.py:161
# Generate companion modules when stagnant.

    def _expansion_mode(self, session: Session, task: str, current_code: str) -> str:
        """Generate companion modules when stagnant."""
        prompt = engineer_improvement_prompt(
            current_code=current_code,
            focus="Explore & Expand: Create a new complementary module or utility that enhances the main codebase while staying true to the original task.",
            task=task,
            focus_name="Expansion",
            iteration=session.iteration_count
        )
        response = self.provider_chain.generate(prompt)
        expanded = extract_code(response, "expansion")
        return expanded or current_code
