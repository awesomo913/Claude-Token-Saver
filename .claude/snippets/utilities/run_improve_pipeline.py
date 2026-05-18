# From: claude_backend/http_server.py:355
# Run prompt_builder pipeline. Returns dict with improved_prompt + estimate.

def run_improve_pipeline(
    prompt: str, project_path: str = "", intent_hint: str = "",
) -> dict:
    """Run prompt_builder pipeline. Returns dict with improved_prompt + estimate.

    Doesn't touch the GUI directly — that's the pending-file's job.
    """
    from .prompt_builder import (
        clean_request, build_smart_prompt, review_prompt, detect_intent,
    )
    from .tokenizer import count_tokens

    cleaned = clean_request(prompt)

    # Pull project conventions if a project was picked.
    project_conventions = ""
    if project_path:
        pp = Path(project_path)
        conv_path = pp / ".claude" / "memory" / "project_conventions.md"
        if conv_path.is_file():
            try:
                project_conventions = conv_path.read_text(encoding="utf-8")[:2000]
            except OSError:
                pass

    code_context, injected_blocks, injected_tokens = _gather_snippet_context(
        project_path, cleaned,
    )

    intent = intent_hint or detect_intent(cleaned)
    improved = build_smart_prompt(
        request=cleaned,
        code_context=code_context,
        project_conventions=project_conventions,
    )
    review = review_prompt(prompt, improved)

    # Each injected snippet is code Claude would otherwise have to
    # regenerate from scratch, so cost ≈ savings.
    if project_path:
        try:
            from .tracker import TokenTracker
            TokenTracker().record(
                operation="improve",
                tokens=injected_tokens,
                project=Path(project_path).name,
                detail=f"snippets={injected_blocks} intent={intent}",
                tokens_avoided=injected_tokens,
            )
        except Exception as e:
            logger.warning("token tracker record failed: %s", e)

    return {
        "improved_prompt": improved,
        "original_tokens": count_tokens(prompt),
        "improved_tokens": review["prompt_tokens"],
        "intent": intent,
        "expansion_ratio": review["expansion_ratio"],
        "impact": review["impact"],
        "injected_snippets": injected_blocks,
        "injected_tokens": injected_tokens,
    }
