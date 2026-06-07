# Complete Module List for NeoAutocoder

## Core Modules (Production-Ready Structure)

### 1. core_loop.py (main heart - ~45KB)
- **Responsibility**: The exact core improvement loop described in the query. Orchestrates: load current codebase, select next focus, engineer prompt (with all fixes), send via provider, extract code, validate (regression/stagnation/identity), save iteration, decide next action (continue, expand, perfect, stop).
- **Key functions**: `run_improvement_loop(session, task, max_iters=0)`, `_engineer_prompt(current_code, focus, task)`, `_process_iteration(response)`, `detect_stagnation(hash_history)`.
- **Incorporates**: All tune-up fixes (90K limit, code-first, incremental language, retrieval fallback, 0.3 regression).

### 2. provider_chain.py (full implementation below)
- **Responsibility**: Ranked fallback chain, ProviderEntry dataclass, cooldown tracking, success/failure metrics, model cycling on interval, API vs CDP abstraction.
- **Key**: `get_next_provider()`, `try_provider_with_fallback(prompt)`, cooldown logic, temperature cycling for API providers.

### 3. session.py
- **Responsibility**: Exact Session dataclass + SessionManager. Manages up to 4 sessions (corner, hwnd, client, queue, executor, active state). Per-session state (iteration_count, focus_history, hash_log, codebase_path).

### 4. cdp_client.py
- **Responsibility**: Chrome DevTools Protocol client over WebSocket. DOM read/write, element finding by multiple selectors, large text insertion (chunked), new_conversation with 30s wait + auto-login + reload fallback. Per-profile selectors (Gemini, OpenRouter, etc.).
- **Includes**: Fixes 6 & 7 from tune-up (extended waits, auto-login from credentials.json/env).

### 5. universal_client.py
- **Responsibility**: Abstraction layer so all providers (API or CDP) quack the same (`generate(prompt) -> str`). Routes to correct backend.

### 6. openrouter_api_client.py
- **Responsibility**: Direct REST API client for OpenRouter. Key from ~/.neoautocoder/openrouter.key. Model rotation from free list (DeepSeek, Qwen, etc.). Temperature cycling.

### 7. ollama_api_client.py
- **Responsibility**: Local Ollama client with Modelfile support (Windows paths).

### 8. fleet_manager.py
- **Responsibility**: Manages the fleet of 4 sessions. Coordinates launch, broadcast, start/stop all, model rotation schedule, global state DB.

### 9. window_manager.py
- **Responsibility**: Win32 API for positioning Chrome windows in 4 screen corners. hwnd tracking.

### 10. ai_profiles.py
- **Responsibility**: AIProfile and CDPSelectors dataclasses. PRESET_PROFILES for Gemini, OpenRouter/chat, Claude, ChatGPT, Copilot. URL patterns, input selectors, send methods (enter vs button), wait multipliers.

### 11. prompt_engineer.py
- **Responsibility**: Builds highly-engineered prompts. Includes project identity lock, code-first directive, incremental language, focus-specific strategies from coding_profiles.py. Retrieval context builder for large codebases.

### 12. code_extractor.py
- **Responsibility**: Robust extraction - regex for ```python, --- FILE: markers, "Python" prefix fallback, LLM judge fallback. Validation (syntax, size >30%, not identical to previous 3).

### 13. recovery_manager.py
- **Responsibility**: Smart recovery - detect non-code response, reset conversation, ask AI to "self-diagnose and provide only the complete code", circuit breaker, Chrome relaunch.

### 14. state_manager.py
- **Responsibility**: SQLite for iteration history, hashes, metrics. JSON snapshots. Resume logic. Auto-start on Windows via registry/task scheduler.

### 15. auto_save.py
- **Responsibility**: Organized saves to `~/Downloads/neoautocoder/<project_slug>/iter_{n:04d}_{focus}_{timestamp}.py` + review.md. Project name extraction from task.

### 16. gui.py
- **Responsibility**: CustomTkinter main app. Session cards showing status/metrics, task input, 8 focus checkboxes (with "Perfection Mode" that cycles all), Start/Stop/Broadcast/Model Rotation Interval controls. Live log pane.

### 17. model_config.py
- **Responsibility**: Loads/saves ~/.neoautocoder/models.json. User settings for rotation interval, selected focuses, cooldowns, expansion rules.

### 18. coding_profiles.py
- **Responsibility**: Maps coding contexts to curated focus lists (10-12 instead of 46). Presets for "Python CLI Tool", "GUI App", "Web Backend", etc.

### 19. run_endless.py
- **Responsibility**: CLI entrypoint for endless worker. Loads state, launches fleet, monitors for KILL file or F10, auto-restart on crash with full recovery.

### 20. launch_cdp_sessions.py
- **Responsibility**: Helper script to launch 1-4 isolated Chrome instances with correct ports (9222-9225), --remote-debugging-port, --remote-allow-origins=*, isolated --user-data-dir=~/.neoautocoder/chrome/<profile>. Mandatory for CDP.

### Supporting
- **requirements.txt**: customtkinter, websocket-client, pywin32, requests, beautifulsoup4 (for extraction fallback), sqlite3 (stdlib).
- **tests/**: unit tests for extractor, prompt engineering, regression guard (TDD enforced).
- **references/**: ARCHITECTURE_DECISIONS.md (this doc), cdp_debug_guide.md, prompt_templates.md.
- **~/.neoautocoder/**: config, keys, credentials.json (gitignored), chrome profiles, state.db, KILL file.

**Total estimated LOC**: ~18,000 (much cleaner than original's monolithic files). Each module has clear single responsibility, comprehensive logging, and verification hooks.

This structure directly implements the original spec while incorporating every lesson from the audit and tune-up skills to make it production-stable.
