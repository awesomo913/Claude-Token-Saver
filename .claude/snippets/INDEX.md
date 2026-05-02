# Snippet Library

## Utilities

- [`get_profile_names`](utilities/get_profile_names.py) (from `ai_profiles.py:202`) -- Get all available profile names (presets + saved custom).
- [`get_profile`](utilities/get_profile.py) (from `ai_profiles.py:211`) -- Get a profile by name. Falls back to Custom if not found.
- [`save_custom_profile`](utilities/save_custom_profile.py) (from `ai_profiles.py:228`) -- Save a custom profile to disk.
- [`load_custom_profiles`](utilities/load_custom_profiles.py) (from `ai_profiles.py:251`) -- Load custom profiles from disk.
- [`engineer_prompt`](utilities/engineer_prompt.py) (from `broadcast.py:53`) -- Use Prompt Architect's engine to build a production-grade prompt.
- [`focus_window`](utilities/focus_window.py) (from `browser_actions.py:59`) -- Bring a window to the foreground.
- [`get_window_rect`](utilities/get_window_rect.py) (from `browser_actions.py:75`) -- Get window position (left, top, right, bottom).
- [`click_chat_input`](utilities/click_chat_input.py) (from `browser_actions.py:87`) -- Click on the AI chat input area using profile offsets.
- [`type_prompt`](utilities/type_prompt.py) (from `browser_actions.py:111`) -- Type text into the focused input via clipboard paste.
- [`send_message`](utilities/send_message.py) (from `browser_actions.py:131`) -- Send the message using the profile's send method.
- [`wait_for_generation_done`](utilities/wait_for_generation_done.py) (from `browser_actions.py:151`) -- Wait for the AI to finish generating.
- [`send_prompt_phase`](utilities/send_prompt_phase.py) (from `browser_actions.py:344`) -- Phase 1: Focus window, click input, paste prompt, send. ~3-5 seconds of mouse use.
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
- [`get_screen_size`](utilities/get_screen_size.py) (from `window_manager.py:40`) -- Get primary monitor resolution.
- [`get_quarter_rect`](utilities/get_quarter_rect.py) (from `window_manager.py:51`) -- Get a 1/4 screen rectangle for a given corner.
- [`find_windows_by_title`](utilities/find_windows_by_title.py) (from `window_manager.py:75`) -- Find ALL visible windows whose title contains the pattern (case-insensitive).
- [`find_chrome_windows`](utilities/find_chrome_windows.py) (from `window_manager.py:105`) -- Backward compat: find Chrome windows.
- [`move_window`](utilities/move_window.py) (from `window_manager.py:112`) -- Move and resize a window by its handle.
- [`position_existing_window`](utilities/position_existing_window.py) (from `window_manager.py:127`) -- Reposition an existing window to a quarter of the screen.

## Classes

- [`AIProfile`](classes/AIProfile.py) (from `ai_profiles.py:17`) -- Describes how to automate a specific AI web chat.
- [`BroadcastConfig`](classes/BroadcastConfig.py) (from `broadcast.py:166`) -- Configuration for a broadcast run.
- [`CDPSelectors`](classes/CDPSelectors.py) (from `cdp_client.py:60`) -- CSS selectors for interacting with a specific AI chat site.
- [`CDPTarget`](classes/CDPTarget.py) (from `cdp_client.py:545`) -- A Chrome/Edge tab available for CDP connection.
- [`Session`](classes/Session.py) (from `session_manager.py:25`) -- One AI browser session — a window, a client, and a task queue.
- [`SmartRouter`](classes/SmartRouter.py) (from `smart_router.py:30`) -- Classify prompts and route between free + Claude sessions.
- [`BrowserGeminiClient`](classes/BrowserGeminiClient.py) (from `universal_client.py:511`) -- Legacy alias — creates a UniversalBrowserClient with Gemini preset.
- [`WindowRect`](classes/WindowRect.py) (from `window_manager.py:24`) -- Screen rectangle.
- [`ScreenInfo`](classes/ScreenInfo.py) (from `window_manager.py:33`) -- Screen dimensions.
- [`TaskClassification`](classes/TaskClassification.py) (from `classifier/types.py:9`) -- Result of classifying a prompt.
- [`SubTask`](classes/SubTask.py) (from `classifier/types.py:22`) -- A single decomposed piece of a prompt.
- [`RoutingResult`](classes/RoutingResult.py) (from `classifier/types.py:31`) -- Complete routing output from the splitter.
- [`ModelInfo`](classes/ModelInfo.py) (from `classifier/types.py:43`) -- Description of an available model.
- [`BackendResponse`](classes/BackendResponse.py) (from `classifier/types.py:53`) -- Response from any AI backend.
- [`SavingsEvent`](classes/SavingsEvent.py) (from `classifier/types.py:65`) -- Single routing event for the tracker.
- [`SavingsSummary`](classes/SavingsSummary.py) (from `classifier/types.py:82`) -- Aggregate savings stats.
- [`ScanConfig`](classes/ScanConfig.py) (from `claude_backend/config.py:21`) -- Configuration for scanning and generation.
- [`ManifestEntry`](classes/ManifestEntry.py) (from `claude_backend/manifest.py:16`) -- A single entry in the generation manifest.
- [`Prefs`](classes/Prefs.py) (from `claude_backend/prefs.py:21`) -- User-facing preferences. Add fields here; defaults always backfilled.
- [`FileEntry`](classes/FileEntry.py) (from `claude_backend/types.py:11`) -- A discovered file from any scanner.

## Patterns

- [`patch_launcher_wrapper`](patterns/patch_launcher_wrapper.py) (from `patch_upstream.py:97`)
- [`patch_build_script`](patterns/patch_build_script.py) (from `patch_upstream.py:131`)
- [`init_sqlite`](patterns/init_sqlite.py) (from `extension_native_bridge/host/claude_native_host.py:86`)
