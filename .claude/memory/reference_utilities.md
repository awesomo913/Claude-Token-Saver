---
name: claude interaction tool Utilities
description: Reusable functions and their locations in claude interaction tool
type: reference
---

# Reusable Functions in claude interaction tool

| Function | Module | Purpose |
|----------|--------|---------|
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
| `save_smart_route_output` | `auto_save.py` | Save combined Smart Route results (free + claude) as one file. |
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
| `HERE` | `build_exe.py` | -- |
| `APP_NAME` | `build_exe.py` | -- |
| `cmd` | `build_exe.py` | -- |
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
| `ROOT` | `patch_upstream.py` | -- |
| `patch_copy_button_layout` | `patch_upstream.py` | -- |
| `patch_launcher_wrapper` | `patch_upstream.py` | -- |
| `patch_build_script` | `patch_upstream.py` | -- |
| `main` | `patch_upstream.py` | -- |
| `logger` | `session_manager.py` | -- |
| `CORNERS` | `session_manager.py` | -- |
| `MAX_SESSIONS` | `session_manager.py` | -- |
| `Session` | `session_manager.py` | One AI browser session — a window, a client, and a task queue. |
| `SessionManager` | `session_manager.py` | Manages up to 4 simultaneous AI browser sessions. |
| `logger` | `smart_router.py` | -- |
| `SMART_ROUTER_AVAILABLE` | `smart_router.py` | -- |
| `FREE_PROFILES` | `smart_router.py` | -- |
| `CLAUDE_PROFILES` | `smart_router.py` | -- |
| `SmartRouter` | `smart_router.py` | Classify prompts and route between free + Claude sessions. |
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
| `main` | `__main__.py` | -- |
| `main` | `ai/__main__.py` | -- |
| `logger` | `classifier/classifier.py` | -- |
| `PromptClassifier` | `classifier/classifier.py` | Classify prompts by complexity and route to free models or Claude. |
| `TaskSplitter` | `classifier/splitter.py` | Split a prompt into free-model and Claude subtasks. |
| `TaskClassification` | `classifier/types.py` | Result of classifying a prompt. |
| `SubTask` | `classifier/types.py` | A single decomposed piece of a prompt. |
| `RoutingResult` | `classifier/types.py` | Complete routing output from the splitter. |
| `ModelInfo` | `classifier/types.py` | Description of an available model. |
| `BackendResponse` | `classifier/types.py` | Response from any AI backend. |
| `SavingsEvent` | `classifier/types.py` | Single routing event for the tracker. |
| `SavingsSummary` | `classifier/types.py` | Aggregate savings stats. |
| `logger` | `claude_backend/auto_inject.py` | -- |
| `SETTINGS_PATH` | `claude_backend/auto_inject.py` | -- |
| `HOOK_ID` | `claude_backend/auto_inject.py` | -- |
| `HOOK_DESCRIPTION` | `claude_backend/auto_inject.py` | -- |
| `check_status` | `claude_backend/auto_inject.py` | Check if auto-inject is installed. Returns status dict. |
| `install` | `claude_backend/auto_inject.py` | Install the SessionStart hook. Returns (success, message). |
| `uninstall` | `claude_backend/auto_inject.py` | Remove the SessionStart hook. Returns (success, message). |
| `logger` | `claude_backend/backend.py` | -- |
| `ClaudeContextManager` | `claude_backend/backend.py` | Main orchestrator for the Claude token saver. |
| `main` | `claude_backend/cli.py` | -- |
| `logger` | `claude_backend/config.py` | -- |
| `DEFAULT_EXTENSIONS` | `claude_backend/config.py` | -- |
| `DEFAULT_IGNORE_DIRS` | `claude_backend/config.py` | -- |
| `ScanConfig` | `claude_backend/config.py` | Configuration for scanning and generation. |
| `load_config` | `claude_backend/config.py` | Load config with layered defaults. |
| `save_config_example` | `claude_backend/config.py` | Write a config example to disk. |
| `logger` | `claude_backend/gui.py` | -- |
| `C` | `claude_backend/gui.py` | -- |
| `F` | `claude_backend/gui.py` | -- |
| `M` | `claude_backend/gui.py` | -- |
| `TEMPLATES` | `claude_backend/gui.py` | -- |
| `AI_TUTORIAL_TEXT` | `claude_backend/gui.py` | -- |
| `TUTORIAL_TEXT` | `claude_backend/gui.py` | -- |
| `TokenSaverApp` | `claude_backend/gui.py` | -- |
| `main` | `claude_backend/gui.py` | -- |
| `logger` | `claude_backend/manifest.py` | -- |
| `ManifestEntry` | `claude_backend/manifest.py` | A single entry in the generation manifest. |
| `Manifest` | `claude_backend/manifest.py` | Tracks generated files for delta updates. |
| `logger` | `claude_backend/ollama_manager.py` | -- |
| `DEFAULT_HOST` | `claude_backend/ollama_manager.py` | -- |
| `RECOMMENDED_MODELS` | `claude_backend/ollama_manager.py` | -- |
| `TURBO_QUANTS` | `claude_backend/ollama_manager.py` | -- |
| `CODING_KEYWORDS` | `claude_backend/ollama_manager.py` | -- |
| `OllamaManager` | `claude_backend/ollama_manager.py` | Manages Ollama models via HTTP API. No pip package needed. |
| `logger` | `claude_backend/prefs.py` | -- |
| `PREFS_PATH` | `claude_backend/prefs.py` | -- |
| `Prefs` | `claude_backend/prefs.py` | User-facing preferences. Add fields here; defaults always backfilled. |
| `ROLES` | `claude_backend/prompt_builder.py` | -- |
| `CONSTRAINTS` | `claude_backend/prompt_builder.py` | -- |
| `REASONING` | `claude_backend/prompt_builder.py` | -- |
| `detect_intent` | `claude_backend/prompt_builder.py` | Detect what the user is trying to do from their request text. |
| `clean_request` | `claude_backend/prompt_builder.py` | Clean up sloppy English in the user's request before it goes to Claude. |
| `build_smart_prompt` | `claude_backend/prompt_builder.py` | Build a lean structured prompt from user request + code context. |
| `review_prompt` | `claude_backend/prompt_builder.py` | Analyze the built prompt for token efficiency. |
| `get_domain` | `claude_backend/search.py` | Get the domain label for a code block based on its file path. |
| `get_domain_color` | `claude_backend/search.py` | Get the badge color for a domain. |
| `get_all_domains` | `claude_backend/search.py` | Get sorted list of unique domains present in the snippets. |
| `score_block` | `claude_backend/search.py` | Score a code block against expanded query terms. |
| `SearchIndex` | `claude_backend/search.py` | Pre-computed inverted index for fast searching over large snippet sets. |
| `smart_search` | `claude_backend/search.py` | Search snippets with fuzzy matching, synonyms, and intent detection. |
| `logger` | `claude_backend/storage.py` | -- |
| `ProjectStorage` | `claude_backend/storage.py` | Manages file storage for a Claude project directory. |
| `logger` | `claude_backend/tokenizer.py` | -- |
| `count_tokens` | `claude_backend/tokenizer.py` | Count tokens accurately with BPE, fallback to heuristic. |
| `has_bpe` | `claude_backend/tokenizer.py` | Check if real BPE tokenizer is available. |
| `logger` | `claude_backend/tracker.py` | -- |
| `TokenTracker` | `claude_backend/tracker.py` | Persistent token savings counter stored in ~/.claude/token_savings.jsonl. |
| `SessionMemory` | `claude_backend/tracker.py` | Tracks what's been sent to Claude in a project's context. |
| `logger` | `claude_backend/tray.py` | -- |
| `ICON_SIZE` | `claude_backend/tray.py` | -- |
| `SNOOZE_FILE` | `claude_backend/tray.py` | -- |
| `build_menu` | `claude_backend/tray.py` | Tray right-click menu. Default item (single-click) opens GUI. |
| `run` | `claude_backend/tray.py` | Start tray icon. Blocks until user picks Quit. |
| `FileEntry` | `claude_backend/types.py` | A discovered file from any scanner. |
| `CodeBlock` | `claude_backend/types.py` | An extracted code block (function, class, etc.). |
| `ModuleInfo` | `claude_backend/types.py` | Information about a Python module. |
| `ConventionReport` | `claude_backend/types.py` | Detected coding conventions. |
| `ProjectAnalysis` | `claude_backend/types.py` | Complete analysis of a project. |
| `GenerationResult` | `claude_backend/types.py` | Result of a generation run. |
| `logger` | `claude_backend/welcome.py` | -- |
| `WELCOME_TITLE` | `claude_backend/welcome.py` | -- |
| `WELCOME_INTRO` | `claude_backend/welcome.py` | -- |
| `WHAT_IT_DOES` | `claude_backend/welcome.py` | -- |
| `PERMISSIONS` | `claude_backend/welcome.py` | -- |
| `QUICK_START` | `claude_backend/welcome.py` | -- |
| `PRO_TIP` | `claude_backend/welcome.py` | -- |
| `WelcomeDialog` | `claude_backend/welcome.py` | Modal welcome window. Closes on dismiss; updates prefs. |
| `show_welcome` | `claude_backend/welcome.py` | Open welcome window. Returns dialog instance (caller can grab focus etc). |
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
| `logger` | `claude_backend/scanners/github.py` | -- |
| `GITHUB_API` | `claude_backend/scanners/github.py` | -- |
| `scan_github_sources` | `claude_backend/scanners/github.py` | Scan configured GitHub sources and return FileEntry list. |
| `logger` | `claude_backend/scanners/local.py` | -- |
| `scan_local_sources` | `claude_backend/scanners/local.py` | Scan configured local source directories. |
| `logger` | `claude_backend/scanners/project.py` | -- |
| `BINARY_CHECK_SIZE` | `claude_backend/scanners/project.py` | -- |
| `scan_project` | `claude_backend/scanners/project.py` | Scan a project directory and return all matching files. |
| `scan_project_fast_mtimes` | `claude_backend/scanners/project.py` | Fast scan that only returns {relative_path: mtime} without reading content. |
| `get_language_stats` | `claude_backend/scanners/project.py` | Count files by extension. |
| `find_entry_points` | `claude_backend/scanners/project.py` | Find likely entry point files. |
| `find_key_files` | `claude_backend/scanners/project.py` | Find important project files that exist at the root. |
| `find_dependencies` | `claude_backend/scanners/project.py` | Extract dependency names from requirements.txt or pyproject.toml. |
| `DATA_DIR` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `LOG_FILE` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `MD_LOG` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `SQLITE_PATH` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `INSERT_FILE` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `logger` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `ensure_data_dir` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `read_message` | `extension_native_bridge/host/claude_native_host.py` | Read one Native Messaging frame from stdin. |
| `write_message` | `extension_native_bridge/host/claude_native_host.py` | Send one frame to Chrome. |
| `init_sqlite` | `extension_native_bridge/host/claude_native_host.py` | -- |
| `HOST_NAME` | `extension_native_bridge/scripts/install_host_windows.py` | -- |
| `main` | `extension_native_bridge/scripts/install_host_windows.py` | -- |
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
| `main` | `gemini_coder_web/__main__.py` | -- |
| `logger` | `gemini_coder_web/ui/app_web.py` | -- |
| `CORNER_LABELS` | `gemini_coder_web/ui/app_web.py` | -- |
| `SessionCard` | `gemini_coder_web/ui/app_web.py` | UI card for one AI session slot (one corner of the screen). |
| `GeminiCoderWebApp` | `gemini_coder_web/ui/app_web.py` | AI Browser Coder - multi-session universal AI automation. |
| `tracker_path` | `scripts/analyze_real_savings.py` | -- |
| `events` | `scripts/analyze_real_savings.py` | -- |
| `PROJECT_SIZES` | `scripts/analyze_real_savings.py` | -- |
| `AVG_FILE_TOKENS` | `scripts/analyze_real_savings.py` | -- |
| `context_builds` | `scripts/analyze_real_savings.py` | -- |
| `bootstraps` | `scripts/analyze_real_savings.py` | -- |
| `preps` | `scripts/analyze_real_savings.py` | -- |
| `copies` | `scripts/analyze_real_savings.py` | -- |
| `tests` | `scripts/analyze_real_savings.py` | -- |
| `total_provided` | `scripts/analyze_real_savings.py` | -- |
| `main` | `scripts/export_all_to_zip.py` | -- |
| `project` | `scripts/full_audit.py` | -- |
| `mgr` | `scripts/full_audit.py` | -- |
| `analysis` | `scripts/full_audit.py` | -- |
| `snippets` | `scripts/full_audit.py` | -- |
| `total_src` | `scripts/full_audit.py` | -- |
| `cm` | `scripts/full_audit.py` | -- |
| `cmd_tok` | `scripts/full_audit.py` | -- |
| `md` | `scripts/full_audit.py` | -- |
| `mem_files` | `scripts/full_audit.py` | -- |
| `mem_tok` | `scripts/full_audit.py` | -- |
| `project` | `scripts/gen_breakdown.py` | -- |
| `mgr` | `scripts/gen_breakdown.py` | -- |
| `analysis` | `scripts/gen_breakdown.py` | -- |
| `snippets` | `scripts/gen_breakdown.py` | -- |
| `total_src` | `scripts/gen_breakdown.py` | -- |
| `cm` | `scripts/gen_breakdown.py` | -- |
| `cmd_tok` | `scripts/gen_breakdown.py` | -- |
| `md` | `scripts/gen_breakdown.py` | -- |
| `mem_tok` | `scripts/gen_breakdown.py` | -- |
| `sd` | `scripts/gen_breakdown.py` | -- |
| `tracker_path` | `scripts/max_plan_public.py` | -- |
| `events` | `scripts/max_plan_public.py` | -- |
| `anon` | `scripts/max_plan_public.py` | -- |
| `project_tokens` | `scripts/max_plan_public.py` | -- |
| `by_op` | `scripts/max_plan_public.py` | -- |
| `by_day` | `scripts/max_plan_public.py` | -- |
| `active_days` | `scripts/max_plan_public.py` | -- |
| `context_events` | `scripts/max_plan_public.py` | -- |
| `total_sent` | `scripts/max_plan_public.py` | -- |
| `total_would` | `scripts/max_plan_public.py` | -- |
| `tracker_path` | `scripts/max_plan_savings.py` | -- |
| `events` | `scripts/max_plan_savings.py` | -- |
| `by_op` | `scripts/max_plan_savings.py` | -- |
| `by_day` | `scripts/max_plan_savings.py` | -- |
| `first_day` | `scripts/max_plan_savings.py` | -- |
| `last_day` | `scripts/max_plan_savings.py` | -- |
| `active_days` | `scripts/max_plan_savings.py` | -- |
| `projects_to_scan` | `scripts/max_plan_savings.py` | -- |
| `project_sizes` | `scripts/max_plan_savings.py` | -- |
| `context_events` | `scripts/max_plan_savings.py` | -- |
| `avg_without` | `scripts/pro_plan_analysis.py` | -- |
| `avg_with` | `scripts/pro_plan_analysis.py` | -- |
| `avg_response` | `scripts/pro_plan_analysis.py` | -- |
| `cw` | `scripts/pro_plan_analysis.py` | -- |
| `exchange_without` | `scripts/pro_plan_analysis.py` | -- |
| `exchange_with` | `scripts/pro_plan_analysis.py` | -- |
| `turns_without` | `scripts/pro_plan_analysis.py` | -- |
| `turns_with` | `scripts/pro_plan_analysis.py` | -- |
| `extra_turns` | `scripts/pro_plan_analysis.py` | -- |
| `input_wo` | `scripts/pro_plan_analysis.py` | -- |
| `tracker_path` | `scripts/session_review.py` | -- |
| `events` | `scripts/session_review.py` | -- |
| `by_day` | `scripts/session_review.py` | -- |
| `total_tok_sent` | `scripts/session_review.py` | -- |
| `total_items` | `scripts/session_review.py` | -- |
| `total_copies` | `scripts/session_review.py` | -- |
| `avg_file` | `scripts/session_review.py` | -- |
| `unique_ratio` | `scripts/session_review.py` | -- |
| `would_read` | `scripts/session_review.py` | -- |
| `saved` | `scripts/session_review.py` | -- |
| `run_cli` | `scripts/smoke_test.py` | -- |
| `main` | `scripts/smoke_test.py` | -- |
| `tracker_path` | `scripts/weekly_projection.py` | -- |
| `events` | `scripts/weekly_projection.py` | -- |
| `by_day` | `scripts/weekly_projection.py` | -- |
| `AVG_FILE` | `scripts/weekly_projection.py` | -- |
| `first` | `scripts/weekly_projection.py` | -- |
| `last` | `scripts/weekly_projection.py` | -- |
| `total_prompts` | `scripts/weekly_projection.py` | -- |
| `total_sent` | `scripts/weekly_projection.py` | -- |
| `total_items` | `scripts/weekly_projection.py` | -- |
| `active_days` | `scripts/weekly_projection.py` | -- |
| `add` | `tests/literag_sample/sample.py` | -- |
| `multiply` | `tests/literag_sample/sample.py` | -- |
| `do_something` | `tests/literag_sample/sample.py` | -- |
| `logger` | `ui/app_web.py` | -- |
| `CORNER_LABELS` | `ui/app_web.py` | -- |
| `SessionCard` | `ui/app_web.py` | UI card for one AI session slot (one corner of the screen). |
| `GeminiCoderWebApp` | `ui/app_web.py` | AI Browser Coder - multi-session universal AI automation. |
