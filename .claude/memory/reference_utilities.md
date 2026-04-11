---
name: claude interaction tool Utilities
description: Reusable functions and their locations in claude interaction tool
type: reference
---

# Reusable Functions in claude interaction tool

| Function | Module | Purpose |
|----------|--------|---------|
| `main` | `__main__.py` | -- |
| `main` | `ai/__main__.py` | -- |
| `logger` | `ai_profiles.py` | -- |
| `AIProfile` | `ai_profiles.py` | Describes how to automate a specific AI web chat. |
| `GEMINI_PROFILE` | `ai_profiles.py` | -- |
| `CHATGPT_PROFILE` | `ai_profiles.py` | -- |
| `CLAUDE_PROFILE` | `ai_profiles.py` | -- |
| `OLLAMA_PROFILE` | `ai_profiles.py` | -- |
| `LMSTUDIO_PROFILE` | `ai_profiles.py` | -- |
| `COPILOT_PROFILE` | `ai_profiles.py` | -- |
| `OPENROUTER_PROFILE` | `ai_profiles.py` | -- |
| `OPENROUTER_FREE_MODELS` | `ai_profiles.py` | -- |
| `logger` | `auto_save.py` | -- |
| `save_task_output` | `auto_save.py` | Save task output to ~/Downloads as a .txt file. |
| `logger` | `broadcast.py` | -- |
| `engineer_prompt` | `broadcast.py` | Use Prompt Architect's engine to build a production-grade prompt. |
| `engineer_improvement_prompt` | `broadcast.py` | Generate an improvement prompt for subsequent iterations. |
| `BroadcastConfig` | `broadcast.py` | Configuration for a broadcast run. |
| `BroadcastController` | `broadcast.py` | Broadcasts a task to multiple sessions and loops improvements. |
| `logger` | `browser_actions.py` | -- |
| `BASE_WAITS` | `browser_actions.py` | -- |
| `MAX_GENERATE_WAIT` | `browser_actions.py` | -- |
| `POST_GENERATE_WAIT` | `browser_actions.py` | -- |
| `focus_window` | `browser_actions.py` | Bring a window to the foreground. |
| `get_window_rect` | `browser_actions.py` | Get window position (left, top, right, bottom). |
| `click_chat_input` | `browser_actions.py` | Click on the AI chat input area using profile offsets. |
| `type_prompt` | `browser_actions.py` | Type text into the focused input via clipboard paste. |
| `send_message` | `browser_actions.py` | Send the message using the profile's send method. |
| `wait_for_generation_done` | `browser_actions.py` | Wait for the AI to finish generating. |
| `logger` | `cdp_client.py` | -- |
| `DEFAULT_CDP_PORT` | `cdp_client.py` | -- |
| `CDP_TIMEOUT` | `cdp_client.py` | -- |
| `COMPLETION_POLL_INTERVAL` | `cdp_client.py` | -- |
| `MAX_COMPLETION_WAIT` | `cdp_client.py` | -- |
| `CDP_CORNER_PORTS` | `cdp_client.py` | -- |
| `get_cdp_port_for_corner` | `cdp_client.py` | Get the CDP port assigned to a screen corner. |
| `CDPSelectors` | `cdp_client.py` | CSS selectors for interacting with a specific AI chat site. |
| `GEMINI_SELECTORS` | `cdp_client.py` | -- |
| `CHATGPT_SELECTORS` | `cdp_client.py` | -- |
| `run_diagnostics` | `cdp_test.py` | Run full CDP diagnostics. |
| `logger` | `claude_backend/analyzers/code_extractor.py` | -- |
| `extract_python_blocks` | `claude_backend/analyzers/code_extractor.py` | Extract functions and classes from Python source using AST. |
| `extract_js_blocks` | `claude_backend/analyzers/code_extractor.py` | Extract function and class blocks from JS/TS source. |
| `extract_blocks` | `claude_backend/analyzers/code_extractor.py` | Extract code blocks based on file extension. |
| `logger` | `claude_backend/analyzers/pattern_detector.py` | -- |
| `MAX_SAMPLES` | `claude_backend/analyzers/pattern_detector.py` | -- |
| `detect_conventions` | `claude_backend/analyzers/pattern_detector.py` | Analyze Python files to detect coding conventions. |
| `logger` | `claude_backend/analyzers/structure_mapper.py` | -- |
| `map_modules` | `claude_backend/analyzers/structure_mapper.py` | Analyze Python files to extract module-level information. |
| `build_import_graph` | `claude_backend/analyzers/structure_mapper.py` | Build a dict mapping module path -> list of internal imports. |
| `logger` | `claude_backend/backend.py` | -- |
| `ClaudeContextManager` | `claude_backend/backend.py` | Main orchestrator for the Claude token saver. |
| `main` | `claude_backend/cli.py` | -- |
| `logger` | `claude_backend/config.py` | -- |
| `DEFAULT_EXTENSIONS` | `claude_backend/config.py` | -- |
| `DEFAULT_IGNORE_DIRS` | `claude_backend/config.py` | -- |
| `ScanConfig` | `claude_backend/config.py` | Configuration for scanning and generation. |
| `load_config` | `claude_backend/config.py` | Load config with layered defaults. |
| `save_config_example` | `claude_backend/config.py` | Write a config example to disk. |
| `logger` | `claude_backend/generators/claude_md.py` | -- |
| `MARKER_START` | `claude_backend/generators/claude_md.py` | -- |
| `MARKER_END` | `claude_backend/generators/claude_md.py` | -- |
| `generate_claude_md` | `claude_backend/generators/claude_md.py` | Generate CLAUDE.md content from a ProjectAnalysis. |
| `write_claude_md` | `claude_backend/generators/claude_md.py` | Write or update CLAUDE.md at the project root. |
| `logger` | `claude_backend/generators/memory_files.py` | -- |
| `compute_project_slug` | `claude_backend/generators/memory_files.py` | Compute the Claude Code project slug from an absolute path. |
| `get_memory_dirs` | `claude_backend/generators/memory_files.py` | Return (claude_code_memory_dir, project_memory_dir). |
| `generate_memory_files` | `claude_backend/generators/memory_files.py` | Generate all memory file contents as a dict of filename -> content. |
| `write_memory_files` | `claude_backend/generators/memory_files.py` | Write memory files to both Claude Code dir and project dir. |
| `logger` | `claude_backend/generators/snippet_library.py` | -- |
| `generate_snippet_library` | `claude_backend/generators/snippet_library.py` | Generate snippet files organized by category. |
| `write_snippet_library` | `claude_backend/generators/snippet_library.py` | Write snippet library to project's .claude/snippets/ directory. |
| `logger` | `claude_backend/manifest.py` | -- |
| `ManifestEntry` | `claude_backend/manifest.py` | A single entry in the generation manifest. |
| `Manifest` | `claude_backend/manifest.py` | Tracks generated files for delta updates. |
| `logger` | `claude_backend/scanners/github.py` | -- |
| `GITHUB_API` | `claude_backend/scanners/github.py` | -- |
| `scan_github_sources` | `claude_backend/scanners/github.py` | Scan configured GitHub sources and return FileEntry list. |
| `logger` | `claude_backend/scanners/local.py` | -- |
| `scan_local_sources` | `claude_backend/scanners/local.py` | Scan configured local source directories. |
| `logger` | `claude_backend/scanners/project.py` | -- |
| `BINARY_CHECK_SIZE` | `claude_backend/scanners/project.py` | -- |
| `scan_project` | `claude_backend/scanners/project.py` | Scan a project directory and return all matching files. |
| `get_language_stats` | `claude_backend/scanners/project.py` | Count files by extension. |
| `find_entry_points` | `claude_backend/scanners/project.py` | Find likely entry point files. |
| `find_key_files` | `claude_backend/scanners/project.py` | Find important project files that exist at the root. |
| `find_dependencies` | `claude_backend/scanners/project.py` | Extract dependency names from requirements.txt or pyproject.toml. |
| `logger` | `claude_backend/storage.py` | -- |
| `ProjectStorage` | `claude_backend/storage.py` | Manages file storage for a Claude project directory. |
| `FileEntry` | `claude_backend/types.py` | A discovered file from any scanner. |
| `CodeBlock` | `claude_backend/types.py` | An extracted code block (function, class, etc.). |
| `ModuleInfo` | `claude_backend/types.py` | Information about a Python module. |
| `ConventionReport` | `claude_backend/types.py` | Detected coding conventions. |
| `ProjectAnalysis` | `claude_backend/types.py` | Complete analysis of a project. |
| `GenerationResult` | `claude_backend/types.py` | Result of a generation run. |
| `AppConfig` | `gemini_coder/config.py` | Application configuration. |
| `ConfigManager` | `gemini_coder/config.py` | Manages application configuration with persistence. |
| `logger` | `gemini_coder/expander.py` | -- |
| `ExpansionEngine` | `gemini_coder/expander.py` | Engine for expanding simple tasks into detailed prompts. |
| `logger` | `gemini_coder/gemini_client.py` | -- |
| `Conversation` | `gemini_coder/gemini_client.py` | Stub conversation class for browser-based clients. |
| `GeminiClient` | `gemini_coder/gemini_client.py` | Stub Gemini client for browser-based automation. |
| `logger` | `gemini_coder/history.py` | -- |
| `HistoryEntry` | `gemini_coder/history.py` | A single entry in the history. |
| `HistoryManager` | `gemini_coder/history.py` | Manages task and conversation history. |
| `detect_platform` | `gemini_coder/platform_utils.py` | Detect the current platform. |
| `get_config_dir` | `gemini_coder/platform_utils.py` | Get the config directory for this application. |
| `get_platform_name` | `gemini_coder/platform_utils.py` | Return a human-readable platform name. |
| `logger` | `gemini_coder/safe_exec.py` | -- |
| `safe_call` | `gemini_coder/safe_exec.py` | Safely call a function, returning default on exception. |
| `safe_exec` | `gemini_coder/safe_exec.py` | Safely execute code, returning the result or None on error. |
| `extract_code_blocks` | `gemini_coder/safe_exec.py` | Extract code blocks from markdown text. |
| `clean_code` | `gemini_coder/safe_exec.py` | Clean extracted code by removing common AI artifacts. |
| `logger` | `gemini_coder/task_manager.py` | -- |
| `TaskStatus` | `gemini_coder/task_manager.py` | Task execution status. |
| `CodingTask` | `gemini_coder/task_manager.py` | A coding task to be executed by an AI agent. |
| `TaskQueue` | `gemini_coder/task_manager.py` | Queue of tasks for a session. |
| `TaskExecutor` | `gemini_coder/task_manager.py` | Executes tasks from a queue using a client. |
| `logger` | `gemini_coder/ui/app.py` | -- |
| `StatusBar` | `gemini_coder/ui/app.py` | Status bar at the bottom of the window. |
| `ToastNotification` | `gemini_coder/ui/app.py` | Toast notification overlay. |
| `GeminiCoderApp` | `gemini_coder/ui/app.py` | Base application class for Gemini Coder desktop app. |
| `SPACING` | `gemini_coder/ui/theme.py` | -- |
| `ICONS` | `gemini_coder/ui/theme.py` | -- |
| `get_colors` | `gemini_coder/ui/theme.py` | Get color scheme based on theme. |
| `main` | `gemini_coder_web/__main__.py` | -- |
| `logger` | `gemini_coder_web/ai_profiles.py` | -- |
| `AIProfile` | `gemini_coder_web/ai_profiles.py` | Describes how to automate a specific AI web chat. |
| `GEMINI_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `CHATGPT_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `CLAUDE_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `OLLAMA_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `LMSTUDIO_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `COPILOT_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `OPENROUTER_PROFILE` | `gemini_coder_web/ai_profiles.py` | -- |
| `OPENROUTER_FREE_MODELS` | `gemini_coder_web/ai_profiles.py` | -- |
| `logger` | `gemini_coder_web/auto_save.py` | -- |
| `save_task_output` | `gemini_coder_web/auto_save.py` | Save task output to ~/Downloads as a .txt file. |
| `GUIBridge` | `gemini_coder_web/bridge.py` | Bridge between the GUI and the backend. |
| `logger` | `gemini_coder_web/broadcast.py` | -- |
| `engineer_prompt` | `gemini_coder_web/broadcast.py` | Use Prompt Architect's engine to build a production-grade prompt. |
| `engineer_improvement_prompt` | `gemini_coder_web/broadcast.py` | Generate an improvement prompt for subsequent iterations. |
| `BroadcastConfig` | `gemini_coder_web/broadcast.py` | Configuration for a broadcast run. |
| `BroadcastController` | `gemini_coder_web/broadcast.py` | Broadcasts a task to multiple sessions and loops improvements. |
| `logger` | `gemini_coder_web/browser_actions.py` | -- |
| `BASE_WAITS` | `gemini_coder_web/browser_actions.py` | -- |
| `MAX_GENERATE_WAIT` | `gemini_coder_web/browser_actions.py` | -- |
| `POST_GENERATE_WAIT` | `gemini_coder_web/browser_actions.py` | -- |
| `focus_window` | `gemini_coder_web/browser_actions.py` | Bring a window to the foreground. |
| `get_window_rect` | `gemini_coder_web/browser_actions.py` | Get window position (left, top, right, bottom). |
| `click_chat_input` | `gemini_coder_web/browser_actions.py` | Click on the AI chat input area using profile offsets. |
| `type_prompt` | `gemini_coder_web/browser_actions.py` | Type text into the focused input via clipboard paste. |
| `send_message` | `gemini_coder_web/browser_actions.py` | Send the message using the profile's send method. |
| `wait_for_generation_done` | `gemini_coder_web/browser_actions.py` | Wait for the AI to finish generating. |
| `logger` | `gemini_coder_web/cdp_client.py` | -- |
| `DEFAULT_CDP_PORT` | `gemini_coder_web/cdp_client.py` | -- |
| `CDP_TIMEOUT` | `gemini_coder_web/cdp_client.py` | -- |
| `COMPLETION_POLL_INTERVAL` | `gemini_coder_web/cdp_client.py` | -- |
| `MAX_COMPLETION_WAIT` | `gemini_coder_web/cdp_client.py` | -- |
| `CDP_CORNER_PORTS` | `gemini_coder_web/cdp_client.py` | -- |
| `get_cdp_port_for_corner` | `gemini_coder_web/cdp_client.py` | Get the CDP port assigned to a screen corner. |
| `CDPSelectors` | `gemini_coder_web/cdp_client.py` | CSS selectors for interacting with a specific AI chat site. |
| `GEMINI_SELECTORS` | `gemini_coder_web/cdp_client.py` | -- |
| `CHATGPT_SELECTORS` | `gemini_coder_web/cdp_client.py` | -- |
| `logger` | `gemini_coder_web/session_manager.py` | -- |
| `CORNERS` | `gemini_coder_web/session_manager.py` | -- |
| `MAX_SESSIONS` | `gemini_coder_web/session_manager.py` | -- |
| `Session` | `gemini_coder_web/session_manager.py` | One AI browser session — a window, a client, and a task queue. |
| `SessionManager` | `gemini_coder_web/session_manager.py` | Manages up to 4 simultaneous AI browser sessions. |
| `logger` | `gemini_coder_web/ui/app_web.py` | -- |
| `CORNER_LABELS` | `gemini_coder_web/ui/app_web.py` | -- |
| `SessionCard` | `gemini_coder_web/ui/app_web.py` | UI card for one AI session slot (one corner of the screen). |
| `GeminiCoderWebApp` | `gemini_coder_web/ui/app_web.py` | AI Browser Coder - multi-session universal AI automation. |
| `logger` | `gemini_coder_web/universal_client.py` | -- |
| `AI_URL_PATTERNS` | `gemini_coder_web/universal_client.py` | -- |
| `UniversalBrowserClient` | `gemini_coder_web/universal_client.py` | Controls ANY AI web chat through browser automation. |
| `BrowserGeminiClient` | `gemini_coder_web/universal_client.py` | Legacy alias — creates a UniversalBrowserClient with Gemini preset. |
| `logger` | `gemini_coder_web/window_manager.py` | -- |
| `WindowRect` | `gemini_coder_web/window_manager.py` | Screen rectangle. |
| `ScreenInfo` | `gemini_coder_web/window_manager.py` | Screen dimensions. |
| `get_screen_size` | `gemini_coder_web/window_manager.py` | Get primary monitor resolution. |
| `get_quarter_rect` | `gemini_coder_web/window_manager.py` | Get a 1/4 screen rectangle for a given corner. |
| `find_windows_by_title` | `gemini_coder_web/window_manager.py` | Find ALL visible windows whose title contains the pattern (case-insensitive). |
| `find_chrome_windows` | `gemini_coder_web/window_manager.py` | Backward compat: find Chrome windows. |
| `move_window` | `gemini_coder_web/window_manager.py` | Move and resize a window by its handle. |
| `position_existing_window` | `gemini_coder_web/window_manager.py` | Reposition an existing window to a quarter of the screen. |
| `find_and_position_window` | `gemini_coder_web/window_manager.py` | Find a window by title pattern and move it to the given corner. |
| `main` | `scripts/export_all_to_zip.py` | -- |
| `run_cli` | `scripts/smoke_test.py` | -- |
| `main` | `scripts/smoke_test.py` | -- |
| `logger` | `session_manager.py` | -- |
| `CORNERS` | `session_manager.py` | -- |
| `MAX_SESSIONS` | `session_manager.py` | -- |
| `Session` | `session_manager.py` | One AI browser session — a window, a client, and a task queue. |
| `SessionManager` | `session_manager.py` | Manages up to 4 simultaneous AI browser sessions. |
| `main` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/__main__.py` | CLI entry point for GUI Builder. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/backend.py` | -- |
| `GUIBuilderBackend` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/backend.py` | Central backend coordinating all GUI Builder operations. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | -- |
| `ExtractedCode` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Result of code extraction from an API response. |
| `MultiFileExtraction` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Result of extracting multiple files from a response. |
| `extract_code` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Extract the primary code block from a Gemini response. |
| `extract_multiple_files` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Extract multiple code files from a response. |
| `inject_main_guard` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Add a main guard to code that lacks one. |
| `strip_markdown` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Remove markdown formatting from a response, keeping only code. |
| `get_required_packages` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/code_extractor.py` | Determine pip packages needed for the code. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `CONFIG_FILE` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `DEFAULT_MODEL` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `AVAILABLE_MODELS` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `SUPPORTED_FRAMEWORKS` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `FRAMEWORK_DISPLAY` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | -- |
| `AppConfig` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | Application configuration with defaults. |
| `ConfigManager` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/config.py` | Load, save, and manage application configuration. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py` | -- |
| `REQUIRED_PACKAGES` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py` | -- |
| `OPTIONAL_PACKAGES` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py` | -- |
| `generate_diagnostic_report` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py` | Generate a comprehensive diagnostic report. |
| `copy_report_to_clipboard` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/diagnostics.py` | Copy the diagnostic report to the system clipboard. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/gemini_client.py` | -- |
| `Message` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/gemini_client.py` | A single message in a conversation. |
| `Conversation` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/gemini_client.py` | A conversation thread for iterative GUI building. |
| `GUIGeminiClient` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/gemini_client.py` | Thread-safe Gemini client optimized for GUI generation tasks. |
| `setup_logging` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/logger_setup.py` | Configure application-wide logging with file and console handlers. |
| `get_recent_errors` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/logger_setup.py` | Read recent error lines from the log file. |
| `APP_DIR_NAME` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | -- |
| `PlatformInfo` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Detected platform information. |
| `detect_platform` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Detect the current platform capabilities. |
| `get_desktop_path` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Get the user's desktop path with fallback. |
| `get_config_dir` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Get the application configuration directory. |
| `get_data_dir` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Get the application data directory for projects. |
| `get_log_dir` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Get the application log directory. |
| `get_templates_dir` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/platform_utils.py` | Get the built-in templates directory. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/preview_runner.py` | -- |
| `PreviewResult` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/preview_runner.py` | Result of a preview execution. |
| `validate_code_safety` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/preview_runner.py` | Check code for potentially dangerous operations before execution. |
| `PreviewRunner` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/preview_runner.py` | Run generated GUI code in a sandboxed subprocess. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py` | -- |
| `ProjectFile` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py` | A single file in a project. |
| `ProjectSnapshot` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py` | A version snapshot of the project. |
| `Project` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py` | A GUI Builder project. |
| `ProjectManager` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/project_manager.py` | Manage project persistence and operations. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | -- |
| `FRAMEWORK_INSTRUCTIONS` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | -- |
| `STYLE_MODIFIERS` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | -- |
| `COMPONENT_CATALOG` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | -- |
| `get_system_instruction` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Get the system instruction for a specific framework. |
| `build_generation_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Build a structured prompt for GUI generation. |
| `build_refinement_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Build a prompt for refining existing GUI code. |
| `build_component_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Build a prompt for adding a component to existing code. |
| `build_layout_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Build a prompt for generating a layout skeleton. |
| `build_clone_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/prompt_engine.py` | Build a prompt for cloning the look of a known application. |
| `logger` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | -- |
| `Template` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | A GUI template definition. |
| `CATEGORIES` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | -- |
| `get_all_templates` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Return all available templates. |
| `get_templates_by_category` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Return templates filtered by category. |
| `get_templates_by_framework` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Return templates compatible with a framework. |
| `get_template_by_id` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Find a template by its ID. |
| `search_templates` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Search templates by name, description, or tags. |
| `get_categories` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Return all template categories. |
| `get_template_count` | `sessions/ClaudeProjects/my_claude_project_ai/gui_builder/gui_builder/template_library.py` | Return total number of templates. |
| `OLLAMA_URL` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/app.py` | -- |
| `generate_response` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/app.py` | Send prompt to Ollama and return the response. |
| `SAFE_RAM_THRESHOLD_MB` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/monitor.py` | -- |
| `CPU_DANGER_THRESHOLD` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/monitor.py` | -- |
| `get_system_health` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/monitor.py` | Returns dict with RAM, CPU, disk stats and overall status. |
| `is_safe_to_generate` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/monitor.py` | Quick check: do we have enough resources to run inference? |
| `OLLAMA_URL` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | -- |
| `CATEGORIES` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | -- |
| `MODEL_PREFERENCES` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | -- |
| `get_available_models` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | Fetch all models from local Ollama. |
| `classify_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | Classify a prompt into a category based on keyword matching. |
| `pick_best_model` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | Given a category and available models, pick the best match. |
| `route_prompt` | `sessions/ClaudeProjects/my_claude_project_ai/local_hub/local_hub/router.py` | Full routing pipeline: classify prompt -> pick model -> return decision. |
| `BG` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `BG_LIGHT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `FG` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `ACCENT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `GREEN` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `RED` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `YELLOW` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `BORDER` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `DIM` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `LocalRelayApp` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py` | -- |
| `JOBS_DIR` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `LOCK_FILE` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `CODE_EXTENSIONS` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `MAX_CHUNK_CHARS` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `PROMPTS` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `SCOPE_PROMPT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `BRIEF_PROMPT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `CHANGELOG_PROMPT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `CHANGELOG_PATTERNS` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `CHANGELOG_GLOB_PATTERNS` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py` | -- |
| `strip_json_fences` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Strip markdown code fences from JSON responses. |
| `cmd_new` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Create a new code analysis job. |
| `cmd_status` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Show current job status. |
| `cmd_process` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Run Qwen preprocessing on all pending files. |
| `cmd_summary` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Generate a compact Claude-ready summary from all processed results. |
| `cmd_feed` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Feed Claude's response back through Qwen for local processing. |
| `cmd_export` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Export the full exchange history. |
| `cmd_close` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | Close the active job and release the lock. |
| `main` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/local_relay.py` | -- |
| `OLLAMA_URL` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | -- |
| `DEFAULT_MODEL` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | -- |
| `TIMEOUT` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | -- |
| `is_available` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | -- |
| `list_models` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | -- |
| `ask_local` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | Send a prompt to the local Ollama model and return the full response text. |
| `ask_local_chat` | `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/ollama_client.py` | Chat-style API for multi-turn exchanges. |
| `BG` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `SURFACE` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `ACCENT` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `PURPLE` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `GREEN` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `RED` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `TEXT` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `FONT` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `FONT_BOLD` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `FONT_MONO` | `sessions/ClaudeProjects/my_claude_project_ai/prompt_architect/prompt_architect/prompt_architect.py` | -- |
| `add` | `sessions/ClaudeProjects/my_claude_project_ai/tests/literag_sample/sample.py` | -- |
| `multiply` | `sessions/ClaudeProjects/my_claude_project_ai/tests/literag_sample/sample.py` | -- |
| `do_something` | `sessions/ClaudeProjects/my_claude_project_ai/tests/literag_sample/sample.py` | -- |
| `add` | `tests/literag_sample/sample.py` | -- |
| `multiply` | `tests/literag_sample/sample.py` | -- |
| `do_something` | `tests/literag_sample/sample.py` | -- |
| `logger` | `ui/app_web.py` | -- |
| `CORNER_LABELS` | `ui/app_web.py` | -- |
| `SessionCard` | `ui/app_web.py` | UI card for one AI session slot (one corner of the screen). |
| `GeminiCoderWebApp` | `ui/app_web.py` | AI Browser Coder - multi-session universal AI automation. |
| `logger` | `universal_client.py` | -- |
| `AI_URL_PATTERNS` | `universal_client.py` | -- |
| `UniversalBrowserClient` | `universal_client.py` | Controls ANY AI web chat through browser automation. |
| `BrowserGeminiClient` | `universal_client.py` | Legacy alias — creates a UniversalBrowserClient with Gemini preset. |
| `logger` | `window_manager.py` | -- |
| `WindowRect` | `window_manager.py` | Screen rectangle. |
| `ScreenInfo` | `window_manager.py` | Screen dimensions. |
| `get_screen_size` | `window_manager.py` | Get primary monitor resolution. |
| `get_quarter_rect` | `window_manager.py` | Get a 1/4 screen rectangle for a given corner. |
| `find_windows_by_title` | `window_manager.py` | Find ALL visible windows whose title contains the pattern (case-insensitive). |
| `find_chrome_windows` | `window_manager.py` | Backward compat: find Chrome windows. |
| `move_window` | `window_manager.py` | Move and resize a window by its handle. |
| `position_existing_window` | `window_manager.py` | Reposition an existing window to a quarter of the screen. |
| `find_and_position_window` | `window_manager.py` | Find a window by title pattern and move it to the given corner. |
