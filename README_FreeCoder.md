# FreeCoder

**Let free AI models do the easy work, save Claude for the hard parts.**

FreeCoder is a browser-automation layer that controls multiple AI chat sites
(Gemini, Claude, ChatGPT, OpenRouter, Copilot, Ollama Web UI) via Chrome
DevTools Protocol (CDP). It classifies every prompt, sends the easy parts to
free models, and chains the results into Claude for the parts that actually
need heavy reasoning.

No API keys. No paid tiers. Uses your already-logged-in browser tabs.

## What It Does

```
Your prompt
    │
    ▼
┌────────────────────────┐
│  Smart Router          │
│  (local classifier,    │
│   no API calls)        │
└────────────────────────┘
    │
    ├── "free"   → Gemini alone, done
    ├── "claude" → Claude alone, done
    └── "split"  → 1. Send easy parts to Gemini
                   2. Inject Gemini's output into Claude prompt
                   3. Send enriched prompt to Claude
                   4. Save both outputs with attribution
```

## Example

Input: *"Create a basic HTML page with a header, sidebar, and dark mode styling.
Then debug the race condition in the WebSocket handler that causes messages to
drop under load."*

FreeCoder splits it:

- `[FREE]` → Gemini handles the HTML/CSS boilerplate
- `[CLAUDE]` → Claude debugs the race condition, with Gemini's HTML as context

Result: one `.txt` file in your Downloads with both outputs labeled by source.

## Features

- **CDP browser automation** — reliable DOM-based control, no pixel clicking
- **Multi-session** — run up to 4 AI chats in parallel (corner-positioned windows)
- **Smart Route** — local classifier decides what's easy vs. hard
- **Hallucination guard** — detects when a free model loses context and stops the loop
- **Auto-save** — every output saved to `~/Downloads/` with attribution headers
- **Plugin system** — pre/post-process hooks (includes PII redactor sample)
- **Live token counter** — real-time cost estimate while typing
- **Fallback chain** — Groq API → OpenRouter API → CDP browser → Ollama local

## Requirements

- Python 3.11+
- Chrome or Edge (launched with `--remote-debugging-port=9222`)
- Dependencies: `customtkinter`, `pyautogui`, `pyperclip`, `websocket-client`

```bash
pip install -r requirements.txt
```

## Quick Start

1. Launch Chrome with CDP enabled:
   ```
   chrome --remote-debugging-port=9222
   ```
2. Open your free AI tabs (e.g., gemini.google.com) and Claude tab
3. Run FreeCoder:
   ```
   python -m claude_interaction_tool
   ```
4. Create sessions for each corner (pick AI profile + window)
5. Check **Smart Route**, type a mixed task, hit **Broadcast**

## How the Classifier Works

Pure Python stdlib, no API calls, no ML model. Scores prompts against weighted
keyword signals loaded from `classifier/data/keywords.json`:

- **FREE signals**: boilerplate, widget layout, data entry, framework ports,
  styling, documentation, renaming, simple CRUD
- **CLAUDE signals**: architecture, debugging, binary protocols, novel
  algorithms, security, complex state, multi-file refactors

Safety check: even when overall routing says "free", sentence-level scanning
catches hidden Claude-level keywords and escalates to "split".

## Architecture

```
claude interaction tool/
├── smart_router.py        # Classify + route between sessions
├── broadcast.py           # Per-session loops, smart_route loop
├── classifier/            # Bundled local classifier (pure stdlib)
│   ├── classifier.py
│   ├── splitter.py
│   ├── types.py
│   └── data/keywords.json
├── cdp_client.py          # Chrome DevTools Protocol WebSocket client
├── universal_client.py    # CDP + pyautogui fallback
├── ai_profiles.py         # Selectors for Gemini, Claude, ChatGPT, etc.
├── session_manager.py     # Multi-corner session coordination
├── auto_save.py           # Downloads folder persistence
└── ui/app_web.py          # CustomTkinter GUI
```

## Why This Beats API-Based Routing

Most prompt-routing tools force you to pay for API tokens on free-tier models
(which are rate-limited and often weaker than the web versions). FreeCoder uses
the **same browser sessions you already have open** — the full-strength Gemini,
ChatGPT, or Claude web UI — through CDP automation. Zero API costs, zero rate
limits beyond what the sites themselves enforce on your account.

## License

MIT
