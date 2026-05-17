# From: claude_backend/search.py:95
# Get sorted list of unique domains present in the snippets.

def get_all_domains(snippets: list[CodeBlock]) -> list[str]:
    """Get sorted list of unique domains present in the snippets."""
    domains = set()
    for b in snippets:
        domains.add(get_domain(b.file_path))
    return sorted(domains)
