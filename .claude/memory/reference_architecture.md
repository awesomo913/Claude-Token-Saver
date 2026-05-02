---
name: claude interaction tool Architecture
description: Module map and dependency graph for claude interaction tool
type: reference
---

# claude interaction tool Architecture

## (root)/

- `__init__.py`: Autocoder - Universal multi-session browser AI automation.
- `__main__.py`: Entry point for Gemini Coder Web Edition. | exports: main
  - imports: ., .ui.app_web
- `ai_profiles.py`: AI profiles for universal browser automation. | exports: logger, AIProfile, GEMINI_PROFILE, CHATGPT_PROFILE, CLAUDE_PROFILE, OLLAMA_PROFILE, LMSTUDIO_PROFILE, COPILOT_PROFILE
- `auto_save.py`: Auto-save task output to Downloads folder as .txt files. | exports: logger, save_task_output, save_smart_route_output
- `broadcast.py`: Broadcast mode — send a task to all active sessions and loop endlessly. | exports: logger, engineer_prompt, engineer_improvement_prompt, BroadcastConfig, BroadcastController
  - imports: .auto_save, .smart_router, .auto_save
- `browser_actions.py`: Low-level browser actions for controlling ANY AI web chat. | exports: logger, BASE_WAITS, MAX_GENERATE_WAIT, POST_GENERATE_WAIT, focus_window, get_window_rect, click_chat_input, type_prompt
  - imports: .ai_profiles
- `browser_client.py`: Backward compatibility — imports from universal_client.
  - imports: .universal_client
- `build_exe.py`: Build script for Claude Token Saver (standalone Windows exe). | exports: HERE, APP_NAME, cmd
- `cdp_client.py`: Chrome DevTools Protocol (CDP) client for browser automation. | exports: logger, DEFAULT_CDP_PORT, CDP_TIMEOUT, COMPLETION_POLL_INTERVAL, MAX_COMPLETION_WAIT, CDP_CORNER_PORTS, get_cdp_port_for_corner, CDPSelectors
  - imports: .window_manager
- `cdp_test.py`: CDP diagnostic and testing utility. | exports: run_diagnostics
  - imports: .cdp_client
- `launch_token_saver.py`: Entry point for PyInstaller — bootstraps claude_backend as a package.
- `launch_tray.py`: Entry point for tray-only mode — runs the system tray icon.
- `patch_upstream.py`: Auto-patcher: applies known fixes to upstream code before building. | exports: ROOT, patch_copy_button_layout, patch_launcher_wrapper, patch_build_script, main
- `session_manager.py`: Session manager — coordinates up to 4 AI browser sessions. | exports: logger, CORNERS, MAX_SESSIONS, Session, SessionManager
  - imports: .ai_profiles, .universal_client
- `smart_router.py`: Smart Router — classifies prompts and chains free models into Claude. | exports: logger, SMART_ROUTER_AVAILABLE, FREE_PROFILES, CLAUDE_PROFILES, SmartRouter
  - imports: .classifier
- `universal_client.py`: Universal browser-based AI client. | exports: logger, AI_URL_PATTERNS, UniversalBrowserClient, BrowserGeminiClient
  - imports: .ai_profiles, .browser_actions, .window_manager, .cdp_client
- `window_manager.py`: Universal window management for AI browser automation. | exports: logger, WindowRect, ScreenInfo, get_screen_size, get_quarter_rect, find_windows_by_title, find_chrome_windows, move_window

## ai/

- `ai/__init__.py`
- `ai/__main__.py` | exports: main

## classifier/

- `classifier/__init__.py`: Bundled prompt classifier (originally from prompt_router).
  - imports: .classifier, .splitter, .types
- `classifier/classifier.py`: Local prompt classifier — determines routing without any API calls. | exports: logger, PromptClassifier
  - imports: .types
- `classifier/splitter.py`: Task splitter — decomposes a mixed prompt into free-model and Claude subtasks. | exports: TaskSplitter
  - imports: .types, .classifier
- `classifier/types.py`: Shared data types for PromptRouter. | exports: TaskClassification, SubTask, RoutingResult, ModelInfo, BackendResponse, SavingsEvent, SavingsSummary

## claude_backend/

- `claude_backend/__init__.py`: Claude Token Saver -- pre-stage project context for Claude Code sessions.
- `claude_backend/__main__.py`: Entry point for python -m claude_backend.
  - imports: .cli
- `claude_backend/analyzers/__init__.py`: Analyzer modules for code extraction and pattern detection.
- `claude_backend/analyzers/code_extractor.py`: Code block extraction using AST for Python and state-machine for JS/TS. | exports: logger, extract_python_blocks, extract_js_blocks, extract_blocks
  - imports: ..types
- `claude_backend/analyzers/pattern_detector.py`: Detect coding conventions and patterns by sampling Python files. | exports: logger, MAX_SAMPLES, detect_conventions
  - imports: ..types
- `claude_backend/analyzers/structure_mapper.py`: Map project structure: modules, imports, public API, entry points. | exports: logger, map_modules, build_import_graph
  - imports: ..types
- `claude_backend/auto_inject.py`: Auto-inject setup: install a Claude Code SessionStart hook. | exports: logger, SETTINGS_PATH, HOOK_ID, HOOK_DESCRIPTION, check_status, install, uninstall
- `claude_backend/backend.py`: ClaudeContextManager: orchestrates scanning, analysis, and generation. | exports: logger, ClaudeContextManager
  - imports: .config, .manifest, .types, .scanners.project, .analyzers.code_extractor
- `claude_backend/cli.py`: CLI interface for Claude token saver. | exports: main
  - imports: .backend, .config, .tray
- `claude_backend/config.py`: Configuration loading with layered defaults. | exports: logger, DEFAULT_EXTENSIONS, DEFAULT_IGNORE_DIRS, ScanConfig, load_config, save_config_example
- `claude_backend/generators/__init__.py`: Generator modules for CLAUDE.md, memory files, and snippet libraries.
- `claude_backend/generators/claude_md.py`: Generate a CLAUDE.md file from project analysis. | exports: logger, MARKER_START, MARKER_END, generate_claude_md, write_claude_md
  - imports: ..types
- `claude_backend/generators/memory_files.py`: Generate Claude Code memory files for persistent cross-session context. | exports: logger, compute_project_slug, get_memory_dirs, generate_memory_files, write_memory_files
  - imports: ..types
- `claude_backend/generators/snippet_library.py`: Extract and organize reusable code snippets into a library. | exports: logger, generate_snippet_library, write_snippet_library
  - imports: ..types
- `claude_backend/gui.py`: Claude Token Saver — standalone GUI for managing project context. | exports: logger, C, F, M, TEMPLATES, AI_TUTORIAL_TEXT, TUTORIAL_TEXT, TokenSaverApp
  - imports: .backend, .config, .generators.memory_files, .ollama_manager, .prefs
- `claude_backend/manifest.py`: Delta-aware manifest for tracking generated files with SHA-256 hashing. | exports: logger, ManifestEntry, Manifest
- `claude_backend/ollama_manager.py`: Ollama model manager — list, pull, delete, select models via HTTP API. | exports: logger, DEFAULT_HOST, RECOMMENDED_MODELS, TURBO_QUANTS, CODING_KEYWORDS, OllamaManager
- `claude_backend/prefs.py`: User preferences for Token Saver GUI — small JSON store. | exports: logger, PREFS_PATH, Prefs
- `claude_backend/prompt_builder.py`: Smart prompt builder — integrates Prompt Architect logic for better prompts. | exports: ROLES, CONSTRAINTS, REASONING, detect_intent, clean_request, build_smart_prompt, review_prompt
  - imports: .tokenizer
- `claude_backend/scanners/__init__.py`: Scanner modules for discovering files from various sources.
- `claude_backend/scanners/github.py`: Optional GitHub scanner for pulling code from public repos. | exports: logger, GITHUB_API, scan_github_sources
  - imports: ..types
- `claude_backend/scanners/local.py`: Local filesystem scanner for additional source directories. | exports: logger, scan_local_sources
  - imports: ..types
- `claude_backend/scanners/project.py`: Project scanner: discovers and catalogs all files in a target project. | exports: logger, BINARY_CHECK_SIZE, scan_project, scan_project_fast_mtimes, get_language_stats, find_entry_points, find_key_files, find_dependencies
  - imports: ..config, ..types
- `claude_backend/search.py`: Fuzzy semantic search engine for code snippets. | exports: get_domain, get_domain_color, get_all_domains, score_block, SearchIndex, smart_search
  - imports: .types
- `claude_backend/storage.py`: Project storage with pathlib, proper logging, and manifest tracking. | exports: logger, ProjectStorage
  - imports: .types
- `claude_backend/tokenizer.py`: Accurate token counting with BPE tokenizer + fast fallback. | exports: logger, count_tokens, has_bpe
- `claude_backend/tracker.py`: Token savings tracker and session context memory. | exports: logger, TokenTracker, SessionMemory
- `claude_backend/tray.py`: System tray icon for Claude Token Saver — passive reminder + quick actions. | exports: logger, ICON_SIZE, SNOOZE_FILE, build_menu, run
  - imports: .auto_inject
- `claude_backend/types.py`: Shared data types for claude_backend. | exports: FileEntry, CodeBlock, ModuleInfo, ConventionReport, ProjectAnalysis, GenerationResult
- `claude_backend/welcome.py`: First-run welcome dialog — explains what Token Saver does, permissions, workflow. | exports: logger, WELCOME_TITLE, WELCOME_INTRO, WHAT_IT_DOES, PERMISSIONS, QUICK_START, PRO_TIP, WelcomeDialog
  - imports: .auto_inject, .prefs

## extension_native_bridge/

- `extension_native_bridge/host/claude_native_host.py`: Chrome Native Messaging host: length-prefixed JSON on stdin/stdout (4-byte little-endian len + UTF-8). | exports: DATA_DIR, LOG_FILE, MD_LOG, SQLITE_PATH, INSERT_FILE, logger, ensure_data_dir, read_message
- `extension_native_bridge/scripts/install_host_windows.py`: Writes the Native Messaging host manifest and registry key for Google Chrome (current user). | exports: HOST_NAME, main

## gemini_coder/

- `gemini_coder/__init__.py`: Gemini Coder core package - browser-based AI coding assistant.
- `gemini_coder/config.py`: Configuration management for Gemini Coder. | exports: AppConfig, ConfigManager
  - imports: .platform_utils
- `gemini_coder/expander.py`: Expander - task expansion for Gemini Coder. | exports: logger, ExpansionEngine
- `gemini_coder/gemini_client.py`: Gemini client module stub for browser-based AI client. | exports: logger, Conversation, GeminiClient
- `gemini_coder/history.py`: History management for Gemini Coder. | exports: logger, HistoryEntry, HistoryManager
  - imports: .platform_utils
- `gemini_coder/platform_utils.py`: Platform utilities for cross-platform support. | exports: detect_platform, get_config_dir, get_platform_name
- `gemini_coder/safe_exec.py`: Safe execution utilities. | exports: logger, safe_call, safe_exec, extract_code_blocks, clean_code
- `gemini_coder/task_manager.py`: Task management for Gemini Coder. | exports: logger, TaskStatus, CodingTask, TaskQueue, TaskExecutor
- `gemini_coder/ui/__init__.py`: UI module for Gemini Coder.
- `gemini_coder/ui/app.py`: Base application class for Gemini Coder. | exports: logger, StatusBar, ToastNotification, GeminiCoderApp
- `gemini_coder/ui/theme.py`: Theme and styling for Gemini Coder UI. | exports: SPACING, ICONS, get_colors

## gemini_coder_web/

- `gemini_coder_web/__init__.py`: Autocoder - Universal multi-session browser AI automation.
- `gemini_coder_web/__main__.py`: Entry point for Gemini Coder Web Edition. | exports: main
  - imports: ., .ui.app_web
- `gemini_coder_web/ai_profiles.py`: AI profiles for universal browser automation. | exports: logger, AIProfile, GEMINI_PROFILE, CHATGPT_PROFILE, CLAUDE_PROFILE, OLLAMA_PROFILE, LMSTUDIO_PROFILE, COPILOT_PROFILE
- `gemini_coder_web/auto_save.py`: Auto-save task output to Downloads folder as .txt files. | exports: logger, save_task_output
- `gemini_coder_web/bridge.py` | exports: GUIBridge
- `gemini_coder_web/broadcast.py`: Broadcast mode — send a task to all active sessions and loop endlessly. | exports: logger, engineer_prompt, engineer_improvement_prompt, BroadcastConfig, BroadcastController
  - imports: .auto_save
- `gemini_coder_web/browser_actions.py`: Low-level browser actions for controlling ANY AI web chat. | exports: logger, BASE_WAITS, MAX_GENERATE_WAIT, POST_GENERATE_WAIT, focus_window, get_window_rect, click_chat_input, type_prompt
  - imports: .ai_profiles
- `gemini_coder_web/browser_client.py`: Backward compatibility — imports from universal_client.
  - imports: .universal_client
- `gemini_coder_web/cdp_client.py`: Chrome DevTools Protocol (CDP) client for browser automation. | exports: logger, DEFAULT_CDP_PORT, CDP_TIMEOUT, COMPLETION_POLL_INTERVAL, MAX_COMPLETION_WAIT, CDP_CORNER_PORTS, get_cdp_port_for_corner, CDPSelectors
  - imports: .window_manager
- `gemini_coder_web/session_manager.py`: Session manager — coordinates up to 4 AI browser sessions. | exports: logger, CORNERS, MAX_SESSIONS, Session, SessionManager
  - imports: .ai_profiles, .universal_client
- `gemini_coder_web/ui/__init__.py`: UI components for Gemini Coder Web Edition.
- `gemini_coder_web/ui/app_web.py`: Autocoder - Universal multi-session browser AI automation. | exports: logger, CORNER_LABELS, SessionCard, GeminiCoderWebApp
  - imports: ..bridge, .., ..ai_profiles, ..session_manager, ..auto_save
- `gemini_coder_web/universal_client.py`: Universal browser-based AI client. | exports: logger, AI_URL_PATTERNS, UniversalBrowserClient, BrowserGeminiClient
  - imports: .ai_profiles, .browser_actions, .window_manager, .cdp_client
- `gemini_coder_web/window_manager.py`: Universal window management for AI browser automation. | exports: logger, WindowRect, ScreenInfo, get_screen_size, get_quarter_rect, find_windows_by_title, find_chrome_windows, move_window

## scripts/

- `scripts/analyze_real_savings.py`: Analyze REAL token savings from actual usage history. | exports: tracker_path, events, PROJECT_SIZES, AVG_FILE_TOKENS, context_builds, bootstraps, preps, copies
- `scripts/export_all_to_zip.py`: Export all current project files to a single zip on the Desktop. | exports: main
- `scripts/full_audit.py`: Full system audit of Claude Token Saver v4.5. | exports: project, mgr, analysis, snippets, total_src, cm, cmd_tok, md
- `scripts/gen_breakdown.py`: Generate technical breakdown txt for external review. | exports: project, mgr, analysis, snippets, total_src, cm, cmd_tok, md
- `scripts/max_plan_public.py`: Public-safe Max Plan savings analysis. All project names anonymized. | exports: tracker_path, events, anon, project_tokens, by_op, by_day, active_days, context_events
- `scripts/max_plan_savings.py`: Hard analysis: how much of the 20x Max Plan this tool saves. | exports: tracker_path, events, by_op, by_day, first_day, last_day, active_days, projects_to_scan
- `scripts/pro_plan_analysis.py`: How much more you get from Claude Pro 20x Max using the Token Saver. | exports: avg_without, avg_with, avg_response, cw, exchange_without, exchange_with, turns_without, turns_with
- `scripts/session_review.py`: Review all sessions, calculate real savings, find improvements. | exports: tracker_path, events, by_day, total_tok_sent, total_items, total_copies, avg_file, unique_ratio
- `scripts/smoke_test.py`: Smoke test for Literag integration and end-to-end flow. | exports: run_cli, main
- `scripts/weekly_projection.py`: Project weekly/monthly savings from actual usage data. | exports: tracker_path, events, by_day, AVG_FILE, first, last, total_prompts, total_sent

## tests/

- `tests/literag_sample/sample.py` | exports: add, multiply, do_something

## ui/

- `ui/__init__.py`: UI components for Gemini Coder Web Edition.
- `ui/app_web.py`: Autocoder - Universal multi-session browser AI automation. | exports: logger, CORNER_LABELS, SessionCard, GeminiCoderWebApp
  - imports: .., ..ai_profiles, ..session_manager, ..auto_save, ..broadcast
