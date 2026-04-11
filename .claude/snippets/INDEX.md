# Snippet Library

## Utilities

- [`get_profile_names`](utilities/get_profile_names.py) (from `ai_profiles.py:202`) -- Get all available profile names (presets + saved custom).
- [`get_profile`](utilities/get_profile.py) (from `ai_profiles.py:211`) -- Get a profile by name. Falls back to Custom if not found.
- [`save_custom_profile`](utilities/save_custom_profile.py) (from `ai_profiles.py:228`) -- Save a custom profile to disk.
- [`load_custom_profiles`](utilities/load_custom_profiles.py) (from `ai_profiles.py:251`) -- Load custom profiles from disk.
- [`_sanitize_filename`](utilities/_sanitize_filename.py) (from `auto_save.py:13`) -- Make a string safe for use as a filename.
- [`engineer_prompt`](utilities/engineer_prompt.py) (from `broadcast.py:39`) -- Use Prompt Architect's engine to build a production-grade prompt.
- [`_get_window_title`](utilities/_get_window_title.py) (from `browser_actions.py:48`) -- Read window title via Win32. Zero impact.
- [`focus_window`](utilities/focus_window.py) (from `browser_actions.py:59`) -- Bring a window to the foreground.
- [`get_window_rect`](utilities/get_window_rect.py) (from `browser_actions.py:75`) -- Get window position (left, top, right, bottom).
- [`click_chat_input`](utilities/click_chat_input.py) (from `browser_actions.py:87`) -- Click on the AI chat input area using profile offsets.
- [`type_prompt`](utilities/type_prompt.py) (from `browser_actions.py:111`) -- Type text into the focused input via clipboard paste.
- [`send_message`](utilities/send_message.py) (from `browser_actions.py:131`) -- Send the message using the profile's send method.
- [`wait_for_generation_done`](utilities/wait_for_generation_done.py) (from `browser_actions.py:151`) -- Wait for the AI to finish generating.
- [`_is_terminal_window`](utilities/_is_terminal_window.py) (from `browser_actions.py:193`) -- Check if the window is a terminal (CMD, PowerShell, Windows Terminal).
- [`send_prompt_phase`](utilities/send_prompt_phase.py) (from `browser_actions.py:344`) -- Phase 1: Focus window, click input, paste prompt, send. ~3-5 seconds of mouse use.
- [`_extract_ai_response`](utilities/_extract_ai_response.py) (from `browser_actions.py:357`) -- Extract just the AI response from full page text.
- [`read_response_phase`](utilities/read_response_phase.py) (from `browser_actions.py:400`) -- Phase 3: Focus window and read the response. ~3-5 seconds of mouse use.
- [`send_prompt_and_get_response`](utilities/send_prompt_and_get_response.py) (from `browser_actions.py:413`) -- Full cycle: send -> wait -> read. Used when NOT using traffic controller.
- [`get_cdp_port_for_corner`](utilities/get_cdp_port_for_corner.py) (from `cdp_client.py:55`) -- Get the CDP port assigned to a screen corner.
- [`get_selectors_for_profile`](utilities/get_selectors_for_profile.py) (from `cdp_client.py:171`) -- Get CDP selectors for a given AI profile name.
- [`discover_cdp_targets`](utilities/discover_cdp_targets.py) (from `cdp_client.py:555`) -- Query Chrome's /json endpoint to find all debuggable tabs.
- [`find_target_by_url`](utilities/find_target_by_url.py) (from `cdp_client.py:589`) -- Find a CDP target whose URL contains the given pattern.
- [`find_target_by_title`](utilities/find_target_by_title.py) (from `cdp_client.py:599`) -- Find a CDP target whose title contains the given pattern.
- [`is_cdp_available`](utilities/is_cdp_available.py) (from `cdp_client.py:609`) -- Check if Chrome is running with remote debugging enabled.
- [`get_chrome_debug_args`](utilities/get_chrome_debug_args.py) (from `cdp_client.py:909`) -- Return Chrome command-line args needed for CDP debugging.
- [`is_chrome_running`](utilities/is_chrome_running.py) (from `cdp_client.py:976`) -- Check if Chrome is currently running.
- [`kill_chrome`](utilities/kill_chrome.py) (from `cdp_client.py:989`) -- Kill all Chrome processes (needed to relaunch with CDP).
- [`connect_to_ai_site`](utilities/connect_to_ai_site.py) (from `cdp_client.py:1003`) -- Find a browser tab matching the AI site and return a chat automation object.
- [`_detect_ai_site`](utilities/_detect_ai_site.py) (from `cdp_test.py:27`) -- Detect which AI site a URL belongs to.
- [`extract_js_blocks`](utilities/extract_js_blocks.py) (from `claude_backend/analyzers/code_extractor.py:107`) -- Extract function and class blocks from JS/TS source.

## Classes

- [`AIProfile`](classes/AIProfile.py) (from `ai_profiles.py:17`) -- Describes how to automate a specific AI web chat.
- [`BroadcastConfig`](classes/BroadcastConfig.py) (from `broadcast.py:146`) -- Configuration for a broadcast run.
- [`CDPSelectors`](classes/CDPSelectors.py) (from `cdp_client.py:60`) -- CSS selectors for interacting with a specific AI chat site.
- [`CDPTarget`](classes/CDPTarget.py) (from `cdp_client.py:545`) -- A Chrome/Edge tab available for CDP connection.
- [`ScanConfig`](classes/ScanConfig.py) (from `claude_backend/config.py:21`) -- Configuration for scanning and generation.
- [`ManifestEntry`](classes/ManifestEntry.py) (from `claude_backend/manifest.py:16`) -- A single entry in the generation manifest.
- [`FileEntry`](classes/FileEntry.py) (from `claude_backend/types.py:11`) -- A discovered file from any scanner.
- [`CodeBlock`](classes/CodeBlock.py) (from `claude_backend/types.py:29`) -- An extracted code block (function, class, etc.).
- [`ModuleInfo`](classes/ModuleInfo.py) (from `claude_backend/types.py:42`) -- Information about a Python module.
- [`ConventionReport`](classes/ConventionReport.py) (from `claude_backend/types.py:53`) -- Detected coding conventions.
- [`ProjectAnalysis`](classes/ProjectAnalysis.py) (from `claude_backend/types.py:66`) -- Complete analysis of a project.
- [`GenerationResult`](classes/GenerationResult.py) (from `claude_backend/types.py:82`) -- Result of a generation run.
- [`AppConfig`](classes/AppConfig.py) (from `gemini_coder/config.py:11`) -- Application configuration.
- [`ConfigManager`](classes/ConfigManager.py) (from `gemini_coder/config.py:26`) -- Manages application configuration with persistence.
- [`Conversation`](classes/Conversation.py) (from `gemini_coder/gemini_client.py:9`) -- Stub conversation class for browser-based clients.
- [`GeminiClient`](classes/GeminiClient.py) (from `gemini_coder/gemini_client.py:30`) -- Stub Gemini client for browser-based automation.
- [`HistoryEntry`](classes/HistoryEntry.py) (from `gemini_coder/history.py:15`) -- A single entry in the history.
- [`HistoryManager`](classes/HistoryManager.py) (from `gemini_coder/history.py:46`) -- Manages task and conversation history.
- [`TaskStatus`](classes/TaskStatus.py) (from `gemini_coder/task_manager.py:15`) -- Task execution status.
- [`CodingTask`](classes/CodingTask.py) (from `gemini_coder/task_manager.py:24`) -- A coding task to be executed by an AI agent.

## Patterns

- [`_build_index`](patterns/_build_index.py) (from `claude_backend/generators/snippet_library.py:108`)
- [`wrapper`](patterns/wrapper.py) (from `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/app.py:164`)
- [`save_job`](patterns/save_job.py) (from `sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py:243`)
