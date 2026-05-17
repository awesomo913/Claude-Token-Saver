# From: claude_backend/prompt_builder.py:160
# Build a lean structured prompt from user request + code context.

def build_smart_prompt(
    request: str,
    code_context: str = "",
    project_conventions: str = "",
) -> str:
    """Build a lean structured prompt from user request + code context.

    Cleans up the user's English before including it — fixes typos,
    capitalizes sentences, adds punctuation. The request should be
    clear to Claude even if the user typed it sloppily.
    """
    sections: list[str] = []

    # Clean up the user's request before including it
    cleaned = clean_request(request)
    sections.append(cleaned)

    if code_context:
        sections.append(
            "Here is the relevant code from my project. "
            "Use these references instead of regenerating:\n\n" + code_context
        )

    if project_conventions:
        sections.append("Follow these project conventions:\n" + project_conventions)

    # The ONE constraint that actually changes behavior
    sections.append("Be concise. Code only — explain in comments, not prose.")

    return "\n\n".join(sections)
