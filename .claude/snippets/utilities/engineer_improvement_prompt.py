# From: broadcast.py:82
# Generate an improvement prompt for subsequent iterations.

def engineer_improvement_prompt(
    task: str,
    iteration: int,
    ai_name: str = "",
) -> str:
    """Generate an improvement prompt for subsequent iterations.

    Cycles through different improvement focuses so each round
    makes the code meaningfully better in a different dimension.
    """
    improvement_focuses = [
        {
            "focus": "Add Features",
            "prompt": (
                "You previously wrote code for: {task}\n\n"
                "Now ADD 2-3 useful features a real user would want:\n"
                "- Config options, CLI arguments, settings\n"
                "- Logging, progress indicators\n"
                "- Input validation, helpful error messages\n"
                "- Any missing functionality\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Professional Polish",
            "prompt": (
                "Improve this code to look and feel professional:\n"
                "- Clean structure, consistent naming\n"
                "- Type hints, docstrings\n"
                "- Organized imports, __main__ block\n"
                "- Polished output/UI\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Robustness & Edge Cases",
            "prompt": (
                "Harden this code for real-world use:\n"
                "- Handle edge cases, empty input, missing files\n"
                "- Add retry logic, graceful shutdown\n"
                "- Resource cleanup, error handling\n"
                "- Validate all inputs\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Performance & Optimization",
            "prompt": (
                "Optimize this code:\n"
                "- Fix bottlenecks, use efficient data structures\n"
                "- Add caching where sensible\n"
                "- Minimize I/O and unnecessary computation\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Final Review & Expand",
            "prompt": (
                "Senior developer final review:\n"
                "- Ensure all features work together\n"
                "- Fix any remaining issues\n"
                "- Add usage examples in comments\n"
                "- Think about what ELSE this could do — add one more capability\n\n"
                "Return the FINAL, COMPLETE code."
            ),
        },
    ]

    idx = iteration % len(improvement_focuses)
    focus = improvement_focuses[idx]
    prompt = focus["prompt"].format(task=task)

    if ai_name:
        prompt = f"[You are {ai_name}] {prompt}"

    return prompt
