<!-- claude-backend:generated:start -->
# claude interaction tool

## Overview

- **Files**: 106 (.py (86), .json (10), .md (6), .js (3), .toml (1))
- **Entry points**: `__main__.py`, `ai/__main__.py`, `cdp_test.py`, `claude_backend/analyzers/structure_mapper.py`, `claude_backend/cli.py`
- **Dependencies**: customtkinter, pyautogui, pyperclip, pystray, Pillow, psutil, websocket-client, customtkinter, pyautogui, pyperclip
- **Key files**: `CLAUDE.md`, `pyproject.toml`, `requirements.txt`

## Structure

```
ai/  (2 files)
claude_backend/  (21 files)
  analyzers/  (4 files)
  generators/  (4 files)
  scanners/  (4 files)
gemini_coder/  (11 files)
  ui/  (3 files)
gemini_coder_web/  (14 files)
  ui/  (2 files)
scripts/  (2 files)
sessions/  (37 files)
  ClaudeProjects/  (37 files)
tests/  (3 files)
  literag_sample/  (3 files)
ui/  (2 files)
```

## Conventions

- Use `pathlib.Path` for all path operations
- Type hints are used extensively -- maintain them
- Uses print() for output (consider migrating to logging)

## Modules

- `ai_profiles.py` -- AI profiles for universal browser automation
- `auto_save.py` -- Auto-save task output to Downloads folder as .txt files
- `broadcast.py` -- Broadcast mode — send a task to all active sessions and loop endlessly
- `browser_actions.py` -- Low-level browser actions for controlling ANY AI web chat
- `browser_client.py` -- Backward compatibility — imports from universal_client
- `cdp_client.py` -- Chrome DevTools Protocol (CDP) client for browser automation
- `cdp_test.py` -- CDP diagnostic and testing utility [entry]
- `claude_backend/analyzers/code_extractor.py` -- Code block extraction using AST for Python and state-machine for JS/TS
- `claude_backend/analyzers/pattern_detector.py` -- Detect coding conventions and patterns by sampling Python files
- `claude_backend/analyzers/structure_mapper.py` -- Map project structure: modules, imports, public API, entry points [entry]
- `claude_backend/backend.py` -- ClaudeContextManager: orchestrates scanning, analysis, and generation
- `claude_backend/cli.py` -- CLI interface for Claude token saver [entry]
- `claude_backend/config.py` -- Configuration loading with layered defaults
- `claude_backend/generators/claude_md.py` -- Generate a CLAUDE.md file from project analysis
- `claude_backend/generators/memory_files.py` -- Generate Claude Code memory files for persistent cross-session context
- `claude_backend/generators/snippet_library.py` -- Extract and organize reusable code snippets into a library
- `claude_backend/manifest.py` -- Delta-aware manifest for tracking generated files with SHA-256 hashing
- `claude_backend/scanners/github.py` -- Optional GitHub scanner for pulling code from public repos
- `claude_backend/scanners/local.py` -- Local filesystem scanner for additional source directories
- `claude_backend/scanners/project.py` -- Project scanner: discovers and catalogs all files in a target project [entry]
- `claude_backend/storage.py` -- Project storage with pathlib, proper logging, and manifest tracking
- `claude_backend/types.py` -- Shared data types for claude_backend
- `gemini_coder/config.py` -- Configuration management for Gemini Coder
- `gemini_coder/expander.py` -- Expander - task expansion for Gemini Coder
- `gemini_coder/gemini_client.py` -- Gemini client module stub for browser-based AI client
- `gemini_coder/history.py` -- History management for Gemini Coder
- `gemini_coder/platform_utils.py` -- Platform utilities for cross-platform support
- `gemini_coder/safe_exec.py` -- Safe execution utilities
- `gemini_coder/task_manager.py` -- Task management for Gemini Coder
- `gemini_coder/ui/app.py` -- Base application class for Gemini Coder
- `gemini_coder/ui/theme.py` -- Theme and styling for Gemini Coder UI
- `gemini_coder_web/ai_profiles.py` -- AI profiles for universal browser automation
- `gemini_coder_web/auto_save.py` -- Auto-save task output to Downloads folder as .txt files
- `gemini_coder_web/bridge.py`
- `gemini_coder_web/broadcast.py` -- Broadcast mode — send a task to all active sessions and loop endlessly
- `gemini_coder_web/browser_actions.py` -- Low-level browser actions for controlling ANY AI web chat
- `gemini_coder_web/browser_client.py` -- Backward compatibility — imports from universal_client
- `gemini_coder_web/cdp_client.py` -- Chrome DevTools Protocol (CDP) client for browser automation
- `gemini_coder_web/session_manager.py` -- Session manager — coordinates up to 4 AI browser sessions
- `gemini_coder_web/ui/app_web.py` -- Autocoder - Universal multi-session browser AI automation

## Snippets

See `.claude/snippets/INDEX.md` for reusable code blocks.

<!-- claude-backend:generated:end -->
