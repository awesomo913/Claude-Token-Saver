# From: broadcast.py:53
# Use Prompt Architect's engine to build a production-grade prompt.

def engineer_prompt(
    task: str,
    build_target: str = "PC Desktop App",
    enhancements: Optional[list[str]] = None,
    context: str = "",
) -> str:
    """Use Prompt Architect's engine to build a production-grade prompt.

    Takes a simple task like "Build a calculator" and expands it into
    a full engineered prompt with role, platform context, reasoning,
    constraints, and quality gates.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        return task

    if enhancements is None:
        enhancements = ["More Features + Robustness"]

    return generate_code_prompt(
        task=task,
        build_target=build_target,
        enhancements=enhancements,
        context=context,
        reasoning="Structured CoT (SCoT)",
        output_format="Code Only",
        constraint_presets=["Python Best Practices", "Robustness"],
    )
