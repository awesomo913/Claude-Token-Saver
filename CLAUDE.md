<!-- claude-backend:generated:start -->
# claude interaction tool

## Overview

- **Files**: 113 (.py (93), .md (11), .json (5), .js (3), .toml (1))
- **Entry points**: `broadcast.py`, `cdp_test.py`, `launch_token_saver.py`, `launch_tray.py`, `patch_upstream.py`
- **Dependencies**: customtkinter, pyautogui, pyperclip, pystray, Pillow, psutil, websocket-client, customtkinter, pyautogui, pyperclip
- **Key files**: `README.md`, `CLAUDE.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`

## Structure

```
ai/  (2 files)
classifier/  (5 files)
  data/  (1 files)
claude_backend/  (31 files)
  analyzers/  (4 files)
  generators/  (4 files)
  scanners/  (4 files)
docs/  (5 files)
  analytics/  (2 files)
extension_native_bridge/  (6 files)
  extension/  (3 files)
  host/  (1 files)
  scripts/  (1 files)
gemini_coder/  (11 files)
  ui/  (3 files)
gemini_coder_web/  (14 files)
  ui/  (2 files)
scripts/  (10 files)
tests/  (3 files)
  literag_sample/  (3 files)
ui/  (2 files)
```

## Conventions

- Use `pathlib.Path` for all path operations
- Type hints are used extensively -- maintain them
- Uses print() for output (consider migrating to logging)
- Absolute imports preferred

## Modules

- `ai_profiles.py` -- AI profiles for universal browser automation
- `auto_save.py` -- Auto-save task output to Downloads folder as .txt files
- `broadcast.py` -- Broadcast mode — send a task to all active sessions and loop endlessly
- `browser_actions.py` -- Low-level browser actions for controlling ANY AI web chat
- `browser_client.py` -- Backward compatibility — imports from universal_client
- `build_exe.py` -- Build script for Claude Token Saver (standalone Windows exe)
- `cdp_client.py` -- Chrome DevTools Protocol (CDP) client for browser automation
- `cdp_test.py` -- CDP diagnostic and testing utility [entry]
- `classifier/classifier.py` -- Local prompt classifier — determines routing without any API calls
- `classifier/splitter.py` -- Task splitter — decomposes a mixed prompt into free-model and Claude subtasks
- `classifier/types.py` -- Shared data types for PromptRouter
- `claude_backend/analyzers/code_extractor.py` -- Code block extraction using AST for Python and state-machine for JS/TS
- `claude_backend/analyzers/pattern_detector.py` -- Detect coding conventions and patterns by sampling Python files
- `claude_backend/analyzers/structure_mapper.py` -- Map project structure: modules, imports, public API, entry points [entry]
- `claude_backend/auto_inject.py` -- Auto-inject setup: install a Claude Code SessionStart hook
- `claude_backend/backend.py` -- ClaudeContextManager: orchestrates scanning, analysis, and generation
- `claude_backend/cli.py` -- CLI interface for Claude token saver [entry]
- `claude_backend/config.py` -- Configuration loading with layered defaults
- `claude_backend/generators/claude_md.py` -- Generate a CLAUDE.md file from project analysis
- `claude_backend/generators/memory_files.py` -- Generate Claude Code memory files for persistent cross-session context
- `claude_backend/generators/snippet_library.py` -- Extract and organize reusable code snippets into a library
- `claude_backend/gui.py` -- Claude Token Saver — standalone GUI for managing project context [entry]
- `claude_backend/manifest.py` -- Delta-aware manifest for tracking generated files with SHA-256 hashing
- `claude_backend/ollama_manager.py` -- Ollama model manager — list, pull, delete, select models via HTTP API
- `claude_backend/prefs.py` -- User preferences for Token Saver GUI — small JSON store
- `claude_backend/prompt_builder.py` -- Smart prompt builder — integrates Prompt Architect logic for better prompts
- `claude_backend/scanners/github.py` -- Optional GitHub scanner for pulling code from public repos
- `claude_backend/scanners/local.py` -- Local filesystem scanner for additional source directories
- `claude_backend/scanners/project.py` -- Project scanner: discovers and catalogs all files in a target project [entry]
- `claude_backend/search.py` -- Fuzzy semantic search engine for code snippets
- `claude_backend/storage.py` -- Project storage with pathlib, proper logging, and manifest tracking
- `claude_backend/tokenizer.py` -- Accurate token counting with BPE tokenizer + fast fallback
- `claude_backend/tracker.py` -- Token savings tracker and session context memory
- `claude_backend/tray.py` -- System tray icon for Claude Token Saver — passive reminder + quick actions [entry]
- `claude_backend/types.py` -- Shared data types for claude_backend
- `claude_backend/welcome.py` -- First-run welcome dialog — explains what Token Saver does, permissions, workflow
- `extension_native_bridge/host/claude_native_host.py` -- Chrome Native Messaging host: length-prefixed JSON on stdin/stdout (4-byte little-endian len + UTF-8) [entry]
- `extension_native_bridge/scripts/install_host_windows.py` -- Writes the Native Messaging host manifest and registry key for Google Chrome (current user) [entry]
- `gemini_coder/config.py` -- Configuration management for Gemini Coder
- `gemini_coder/expander.py` -- Expander - task expansion for Gemini Coder

## Snippets

See `.claude/snippets/INDEX.md` for reusable code blocks.

<!-- claude-backend:generated:end -->
