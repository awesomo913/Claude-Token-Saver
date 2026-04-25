"""GitHub App Installer -- pre-stage project context for Claude Code sessions.

Scans a project, analyzes code patterns, and generates:
- CLAUDE.md with project overview and conventions
- Memory files for persistent cross-session context
- Snippet library of reusable code blocks

Usage:
    python -m claude_backend bootstrap <project_path>
    python -m claude_backend prep <project_path>
    python -m claude_backend scan <project_path>
    python -m claude_backend status <project_path>
    python -m claude_backend clean <project_path>
"""

__version__ = "4.5.0"
__app_name__ = "GitHub App Installer"

__all__ = ["backend", "config", "types"]
