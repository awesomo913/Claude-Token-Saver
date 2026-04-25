# Claude: Extension + Native Messaging (CDP alternative)

This folder implements the **Extension + Native Messaging** pattern so you can capture Claude web chat to local disk **without** Chrome DevTools Protocol (`--remote-debugging-port`).

## Why not CDP alone?

**The Chrome startup dependency:** CDP needs Chrome running with something like `--remote-debugging-port=9222`. If you launch Chrome normally, open a link from another app, or Chrome updates, that port is not bound. A tool that expects CDP can fail to attach **silently**, and you lose session history and automation.

**The moving target:** Intercepting Anthropic’s network (minified payloads, WebSockets, SSE) breaks whenever the web app changes. Reading `Network.responseReceived` is fragile.

**Tab freezing:** Inactive tabs are throttled; CDP can drop or stall. Reconnecting across many sleeping tabs is painful.

**The higher-expected-value path:** A small **Chrome extension** (observer on the real `claude.ai` DOM) plus a **Native Messaging host** (official Chrome API: `chrome.runtime.sendNativeMessage` / `connectNative`) and a local **Python process** (stdin JSON frames) gives stable I/O to disk and optional push-back into the composer.

**Trade-off:** A one-time install (host manifest + registry on Windows) in exchange for stability and no debug port.

---

## What this build does

| Piece | Role |
|--------|------|
| **Extension** | Content script on `claude.ai` uses `MutationObserver` / `data-is-streaming` (same signals as your `CLAUDE_SELECTORS` in `cdp_client.py`) to detect **finished** assistant text — no network parsing. |
| **Native bridge** | Length-prefixed JSON on stdin/stdout per Chrome’s Native Messaging spec. |
| **Local host** (`host/claude_native_host.py`) | Appends to markdown, records rows in SQLite, optional **insert** into the page via a small JSON file (see below). |

Data directory (default):

`%APPDATA%\claude_token_saver\extension_bridge\`

- `claude_messages.md` — running log  
- `messages.sqlite` — queryable table `assistant_messages`  
- `insert_request.json` — drop `{"text":"..."}` to insert into Claude’s ProseMirror input (host forwards to the extension)  
- `bridge.log` — host log  

---

## Install (Windows + Chrome)

1. **Load the unpacked extension**  
   - Chrome → Extensions → Developer mode → Load unpacked.  
   - Select folder `extension_native_bridge/extension/`.  
   - Copy the **extension ID** (32 characters).

2. **Register the native host**  
   From a terminal:

   ```text
   cd extension_native_bridge\scripts
   py -3 install_host_windows.py YOUR_EXTENSION_ID
   ```

   This writes `host/com.claudetools.bridge.json` and sets  
   `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.claudetools.bridge`  
   to that JSON path.

3. **Reload the extension** and open `https://claude.ai/`. The service worker calls `connectNative` on start; the first captured assistant message should appear in `claude_messages.md`.

4. **Microsoft Edge** (optional): add the same manifest under  
   `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.claudetools.bridge`  
   (same JSON file path is fine).

## Linux / macOS (Chrome)

- Place `com.claudetools.bridge.json` in  
  `~/.config/google-chrome/NativeMessagingHosts/` (Linux) or  
  `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/` (macOS).  
- Set `path` to a wrapper that runs `python3 claude_native_host.py` (absolute paths).  
- `allowed_origins` must list `chrome-extension://<id>/`.

---

## Hotkey / external tool → insert text

1. Open a `claude.ai` tab (so the extension is connected to the host).  
2. Write (or have another tool write):

   `%APPDATA%\claude_token_saver\extension_bridge\insert_request.json`

   ```json
   { "text": "Pasted from my local context tool…" }
   ```

3. The host picks it up, sends `insert_text` to the extension, and the content script inserts into the ProseMirror field (`execCommand('insertText')` with fallback).

This matches the “global hotkey → local daemon → extension inserts” flow: bind your hotkey to a small script that only writes that JSON file.

---

## Security notes

- The extension is scoped to `claude.ai` in the manifest.  
- Only your extension ID in `allowed_origins` can launch the host.  
- Do not commit secrets; the host only reads project-local JSON.

---

## Files

- `extension/manifest.json` — MV3, content script, service worker, `nativeMessaging`  
- `extension/content_claude.js` — DOM completion detection + insert  
- `extension/service_worker.js` — `connectNative`, forwards messages, insert routing  
- `host/claude_native_host.py` — stdio native host + SQLite + optional insert file  
- `host/run_host.cmd` — Windows launcher (Chrome’s `path` can point to this)  
- `scripts/install_host_windows.py` — manifest + registry helper  

---

## If something fails

- **“Specified native messaging host not found”**  
  Re-run `install_host_windows.py` with the **current** extension ID (it changes if you re-load a new unpacked folder).  
- **No lines in `claude_messages.md`**  
  Check `bridge.log` in the data directory and `host/host_stderr.log` next to `run_host.cmd`.  
- **Selectors changed**  
  Update `content_claude.js` to match the current [data-is-streaming] / assistant markup (align with `CLAUDE_SELECTORS` in `gemini_coder_web/cdp_client.py`).

This stack is the stable complement to the older CDP-based path in the rest of the repo: use **DOM + Native Messaging** for production capture, CDP for optional automation experiments.
