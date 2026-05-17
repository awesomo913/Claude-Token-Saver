# From: claude_backend/search.py:80
# Get the domain label for a code block based on its file path.

def get_domain(file_path: str) -> str:
    """Get the domain label for a code block based on its file path."""
    fp = file_path.lower().replace("\\", "/")
    # Check longest matches first (mod_ prefix)
    for pattern, domain in FILE_DOMAINS.items():
        if pattern in fp:
            return domain
    return "Other"
