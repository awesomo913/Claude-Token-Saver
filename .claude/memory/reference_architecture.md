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
- `auto_save.py`: Auto-save task output to Downloads folder as .txt files. | exports: logger, save_task_output
- `broadcast.py`: Broadcast mode — send a task to all active sessions and loop endlessly. | exports: logger, engineer_prompt, engineer_improvement_prompt, BroadcastConfig, BroadcastController
  - imports: .auto_save
- `browser_actions.py`: Low-level browser actions for controlling ANY AI web chat. | exports: logger, BASE_WAITS, MAX_GENERATE_WAIT, POST_GENERATE_WAIT, focus_window, get_window_rect, click_chat_input, type_prompt
  - imports: .ai_profiles
- `browser_client.py`: Backward compatibility — imports from universal_client.
  - imports: .universal_client
- `cdp_client.py`: Chrome DevTools Protocol (CDP) client for browser automation. | exports: logger, DEFAULT_CDP_PORT, CDP_TIMEOUT, COMPLETION_POLL_INTERVAL, MAX_COMPLETION_WAIT, CDP_CORNER_PORTS, get_cdp_port_for_corner, CDPSelectors
  - imports: .window_manager
- `cdp_test.py`: CDP diagnostic and testing utility. | exports: run_diagnostics
  - imports: .cdp_client
- `session_manager.py`: Session manager — coordinates up to 4 AI browser sessions. | exports: logger, CORNERS, MAX_SESSIONS, Session, SessionManager
  - imports: .ai_profiles, .universal_client
- `universal_client.py`: Universal browser-based AI client. | exports: logger, AI_URL_PATTERNS, UniversalBrowserClient, BrowserGeminiClient
  - imports: .ai_profiles, .browser_actions, .window_manager, .cdp_client
- `window_manager.py`: Universal window management for AI browser automation. | exports: logger, WindowRect, ScreenInfo, get_screen_size, get_quarter_rect, find_windows_by_title, find_chrome_windows, move_window

## ai/

- `ai/__init__.py`
- `ai/__main__.py` | exports: main

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
- `claude_backend/backend.py`: ClaudeContextManager: orchestrates scanning, analysis, and generation. | exports: logger, ClaudeContextManager
  - imports: .config, .manifest, .types, .scanners.project, .analyzers.code_extractor
- `claude_backend/cli.py`: CLI interface for Claude token saver. | exports: main
  - imports: .backend, .config
- `claude_backend/config.py`: Configuration loading with layered defaults. | exports: logger, DEFAULT_EXTENSIONS, DEFAULT_IGNORE_DIRS, ScanConfig, load_config, save_config_example
- `claude_backend/generators/__init__.py`: Generator modules for CLAUDE.md, memory files, and snippet libraries.
- `claude_backend/generators/claude_md.py`: Generate a CLAUDE.md file from project analysis. | exports: logger, MARKER_START, MARKER_END, generate_claude_md, write_claude_md
  - imports: ..types
- `claude_backend/generators/memory_files.py`: Generate Claude Code memory files for persistent cross-session context. | exports: logger, compute_project_slug, get_memory_dirs, generate_memory_files, write_memory_files
  - imports: ..types
- `claude_backend/generators/snippet_library.py`: Extract and organize reusable code snippets into a library. | exports: logger, generate_snippet_library, write_snippet_library
  - imports: ..types
- `claude_backend/manifest.py`: Delta-aware manifest for tracking generated files with SHA-256 hashing. | exports: logger, ManifestEntry, Manifest
- `claude_backend/scanners/__init__.py`: Scanner modules for discovering files from various sources.
- `claude_backend/scanners/github.py`: Optional GitHub scanner for pulling code from public repos. | exports: logger, GITHUB_API, scan_github_sources
  - imports: ..types
- `claude_backend/scanners/local.py`: Local filesystem scanner for additional source directories. | exports: logger, scan_local_sources
  - imports: ..types
- `claude_backend/scanners/project.py`: Project scanner: discovers and catalogs all files in a target project. | exports: logger, BINARY_CHECK_SIZE, scan_project, get_language_stats, find_entry_points, find_key_files, find_dependencies
  - imports: ..config, ..types
- `claude_backend/storage.py`: Project storage with pathlib, proper logging, and manifest tracking. | exports: logger, ProjectStorage
  - imports: .types
- `claude_backend/types.py`: Shared data types for claude_backend. | exports: FileEntry, CodeBlock, ModuleInfo, ConventionReport, ProjectAnalysis, GenerationResult

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

- `scripts/export_all_to_zip.py`: Export all current project files to a single zip on the Desktop. | exports: main
- `scripts/smoke_test.py`: Smoke test for Literag integration and end-to-end flow. | exports: run_cli, main

## sessions/

- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/__init__.py`: GUI Builder - AI-powered GUI generation tool using Google Gemini.
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/__main__.py`: GUI Builder entry point — CLI interface for the backend. | exports: main
  - imports: ., .backend, .code_extractor
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/backend.py`: Backend orchestrator — single entry point for all backend operations. | exports: logger, GUIBuilderBackend
  - imports: .config, .gemini_client, .code_extractor, .template_library, .project_manager
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py`: Extract and validate code from Gemini API responses. | exports: logger, ExtractedCode, MultiFileExtraction, extract_code, extract_multiple_files, inject_main_guard, strip_markdown, get_required_packages
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py`: Configuration management with auto-save and validation. | exports: logger, CONFIG_FILE, DEFAULT_MODEL, AVAILABLE_MODELS, SUPPORTED_FRAMEWORKS, FRAMEWORK_DISPLAY, AppConfig, ConfigManager
  - imports: .platform_utils
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py`: Diagnostic report generation. | exports: logger, REQUIRED_PACKAGES, OPTIONAL_PACKAGES, generate_diagnostic_report, copy_report_to_clipboard
  - imports: ., .platform_utils, .logger_setup
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/gemini_client.py`: Google Gemini API client specialized for GUI code generation. | exports: logger, Message, Conversation, GUIGeminiClient
  - imports: .prompt_engine, .prompt_engine, .prompt_engine
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/logger_setup.py`: Logging configuration with rotating file handler. | exports: setup_logging, get_recent_errors
  - imports: .platform_utils
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py`: Platform detection and path utilities. | exports: APP_DIR_NAME, PlatformInfo, detect_platform, get_desktop_path, get_config_dir, get_data_dir, get_log_dir, get_templates_dir
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/preview_runner.py`: Sandbox preview runner for generated GUI code. | exports: logger, PreviewResult, validate_code_safety, PreviewRunner
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py`: Project management: save, load, export, and version GUI projects. | exports: logger, ProjectFile, ProjectSnapshot, Project, ProjectManager
  - imports: .platform_utils, .code_extractor
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py`: Prompt engineering for GUI code generation. | exports: logger, FRAMEWORK_INSTRUCTIONS, STYLE_MODIFIERS, COMPONENT_CATALOG, get_system_instruction, build_generation_prompt, build_refinement_prompt, build_component_prompt
  - imports: .config
- `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py`: Built-in GUI template library for quick-start generation. | exports: logger, Template, CATEGORIES, get_all_templates, get_templates_by_category, get_templates_by_framework, get_template_by_id, search_templates
- `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/app.py`: Local AI Hub - MoE Router + Hardware Monitor + Chat Interface. | exports: OLLAMA_URL, generate_response
- `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/monitor.py`: System health monitor for local AI inference safety. | exports: SAFE_RAM_THRESHOLD_MB, CPU_DANGER_THRESHOLD, get_system_health, is_safe_to_generate
- `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py`: MoE-style prompt router that classifies prompts and picks the best local model. | exports: OLLAMA_URL, CATEGORIES, MODEL_PREFERENCES, get_available_models, classify_prompt, pick_best_model, route_prompt
- `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py`: LocalRelay — Desktop GUI for the local LLM pipeline. | exports: BG, BG_LIGHT, FG, ACCENT, GREEN, RED, YELLOW, BORDER
- `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | exports: JOBS_DIR, LOCK_FILE, CODE_EXTENSIONS, MAX_CHUNK_CHARS, PROMPTS, SCOPE_PROMPT, BRIEF_PROMPT, CHANGELOG_PROMPT
- `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py`: LocalRelay — Pipeline between local Qwen (Ollama) and Claude for code analysis. | exports: strip_json_fences, cmd_new, cmd_status, cmd_process, cmd_summary, cmd_feed, cmd_export, cmd_close
- `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | exports: OLLAMA_URL, DEFAULT_MODEL, TIMEOUT, is_available, list_models, ask_local, ask_local_chat
- `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py`: Advanced Prompt Architect — DEPTH + SCoT Prompt Builder | exports: BG, SURFACE, ACCENT, PURPLE, GREEN, RED, TEXT, FONT
- `sessions/ClaudeProjects/my_claude_project_ai/tests/literag_sample/sample.py` | exports: add, multiply, do_something

## tests/

- `tests/literag_sample/sample.py` | exports: add, multiply, do_something

## ui/

- `ui/__init__.py`: UI components for Gemini Coder Web Edition.
- `ui/app_web.py`: Autocoder - Universal multi-session browser AI automation. | exports: logger, CORNER_LABELS, SessionCard, GeminiCoderWebApp
  - imports: .., ..ai_profiles, ..session_manager, ..auto_save, ..broadcast
