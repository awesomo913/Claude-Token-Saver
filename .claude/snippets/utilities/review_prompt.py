# From: claude_backend/prompt_builder.py:192
# Analyze the built prompt for token efficiency.

def review_prompt(original_request: str, final_prompt: str) -> dict:
    """Analyze the built prompt for token efficiency."""
    prompt_tokens = count_tokens(final_prompt)
    request_tokens = max(count_tokens(original_request), 1)
    ratio = prompt_tokens / request_tokens

    if prompt_tokens < 500:
        impact = "LIGHT"
    elif prompt_tokens < 2000:
        impact = "MODERATE"
    elif prompt_tokens < 8000:
        impact = "LARGE"
    else:
        impact = "VERY LARGE"

    return {
        "prompt_tokens": prompt_tokens,
        "request_tokens": request_tokens,
        "expansion_ratio": round(ratio, 1),
        "impact": impact,
        "sections": final_prompt.count("\n# ") + (1 if final_prompt.startswith("# ") else 0),
    }
