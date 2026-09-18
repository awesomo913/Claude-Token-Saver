# Claude Token Saver

> A Windows desktop tool that pre-stages targeted code snippets for Claude Code, so it reads a few relevant blocks instead of whole files.

Claude Token Saver scans a codebase, breaks it into searchable blocks (classes, functions, patterns), and lets you pull just the pieces a coding session needs into a queue that gets copied straight into the chat. The measured effect on its own 131-file codebase: 5.9x compression, 82% average token reduction per query, and 90% search accuracy even on typo-filled queries.

## Features
- **Context extraction** — scans a project and breaks it into snippet blocks (classes, patterns, utilities) with a searchable index
- **Real BPE tokenizer** — uses tiktoken (Rust-backed) instead of a character-count heuristic, 6–35% more accurate on code/JSON/regex
- **Delta caching** — `prep` skips regeneration when nothing changed (measured 428x faster on an unchanged project)
- **Fuzzy search** — finds the right snippet even on sloppy/typo-filled queries
- **Queue cap + copy debounce** — caps the request queue at 15 snippets and blocks duplicate copies within 2 seconds
- **Domain-organized browsing** — snippets grouped by area (Browser, Config, Search, etc.) with colored badges
- **System tray app** — runs from the tray (CustomTkinter + pystray), with optional auto-launch hooks for Claude Code sessions

## Stack
Python 3.10+ · CustomTkinter (GUI) · tiktoken · pyautogui / pyperclip (clipboard automation) · pystray (tray icon) · websocket-client (CDP browser automation).

## Getting started
**Requirements**
- Python 3.10+, Windows (uses pyautogui/pystray for desktop automation)

**Run**
```bash
pip install -r requirements.txt
python launch_token_saver.py
# tray-only launcher:
python launch_tray.py
```

## Status
**Unmaintained / archived.** Personal project, published as-is — fork it, adapt it, take it over. No support or guarantees.

## License
[MIT](LICENSE) — free to use, fork, and build on.
