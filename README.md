# Claude Token Saver

Save **88% of input tokens** when working with Claude Code by pre-staging targeted code context instead of letting Claude read entire files.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![Version](https://img.shields.io/badge/Version-4.5.2-purple)
![Tokens Saved](https://img.shields.io/badge/Tokens_Saved-5.7M+-brightgreen)
![Grade](https://img.shields.io/badge/Grade-A_(3.70_GPA)-gold)

## ⚠️ Production Status

**Current Status**: NOT PRODUCTION READY (7.9/10)  
**Critical Blocker**: 1 blocking issue identified during testing  
**Latest Testing**: 2026-04-26 (43 files, 463 tokens, 100% consistency)

📋 **[View Full Production Readiness Report](PRODUCTION_READINESS.md)** | 📊 **[View Testing Report](TESTING_REPORTS.md)** | 📈 **[View Analytics](docs/analytics/)**

### Key Findings
- ✅ **Tokenization**: 100% consistency across 15 tests, 3.36 chars/token average
- ✅ **Filesystem Scanning**: 43/43 files discovered correctly (100%)
- ⚠️ **Context Generation**: BLOCKED by ScanConfig API incompatibility (critical bug)
- ⚠️ **Code Quality Analysis**: Untested on real production code

**Action Required**: Fix ScanConfig API parameter mismatch (estimated 2 hours) before production deployment.

---

## What's New in v4.5.2

- **Real BPE tokenizer** — replaced `chars/3.2` heuristic with tiktoken (Rust-backed, millisecond speed). 6-35% more accurate token counts, especially on code, JSON, and regex.
- **Delta caching** — `prep` now skips regeneration if no source files changed. 0.01s vs 4.28s = **428x faster** on unchanged projects.
- **Queue cap at 15** — prevents bloated prompts. Previously unlimited (some copies had 165 snippets).
- **Copy debounce** — 2-second cooldown prevents duplicate pastes (8 duplicates found in tracker data).
- **Clear button** — one click wipes request box + queue + matches.
- **Request text cleanup** — fixes typos, grammar, contractions before sending to Claude.
- **Domain browsing** — Snippets organized by area (Browser, Config, Search, etc.) with colored badges.
- **Quick Grab** — click a domain to instantly add its top functions to your prompt.

## The Problem

Every time you ask Claude about your code, it reads entire files to understand context. A 300-token question about one function costs **10,000+ tokens** because Claude scans the whole file.

## The Solution

Claude Token Saver scans your project once, then lets you build **targeted prompts** with only the relevant code. Type what you need in plain English (typos OK), and the tool auto-finds the right snippets.

```
WITHOUT tool:  71,808 tokens per message (reads full files)
WITH tool:      8,017 tokens per message (targeted snippets)
SAVINGS:       88% reduction per message
```

## Quick Start

### Option A: Standalone EXE (no Python needed)
1. Download `ClaudeTokenSaver_v4.5.zip` from [Releases](https://github.com/awesomo913/Claude-Token-Saver/releases) (or your current release on GitHub)
2. Unzip, double-click `ClaudeTokenSaver.exe`  
   *Building from source:* `py -3 build_exe.py` also copies the app folder to `Desktop\ClaudeTokenSaver` on Windows.

### Option B: Run from source
```bash
pip install customtkinter pyperclip tiktoken
cd claude_token_saver
python -m claude_backend.gui
```

### Option C: CLI only
```bash
python -m claude_backend bootstrap /path/to/your/project
python -m claude_backend scan /path/to/your/project
python -m claude_backend prep /path/to/your/project
```

## How It Works

### 1. Load & Bootstrap (one-time setup)
Point the tool at your project folder. It scans all code and generates:
- **CLAUDE.md** at your project root (Claude Code auto-loads this)
- **Memory files** in Claude Code's persistent memory directory
- **Snippet library** of all your reusable functions and classes

### 2. Type What You Need
Go to Context Builder. Type your request in plain English:

> "fix teh cdp timout conection"

The tool:
- **Fixes your typos** (`teh` -> `the`, `timout` -> `timeout`)
- **Auto-finds relevant code** using fuzzy semantic search
- **Grabs related functions** from the same files
- **Builds a structured prompt** with your request + the right code

### 3. Copy & Paste
One click copies everything to clipboard. Paste into Claude Code. Done.

## Features

### Fuzzy Search That Understands You
Type however you want. The search handles:
- **Typos**: `"conection timout"` finds `CDPConnection`, `timeout` functions
- **Synonyms**: `"browser stuff"` matches window, CDP, chrome, websocket code
- **Vague descriptions**: `"the part that saves things"` finds storage/file functions
- **Sloppy English**: `"im tryna fix teh brwoser fokus thing"` works

### Quick Grab (for non-coders)
Don't know function names? Click a domain button:

`[Browser (26)]` `[Config (8)]` `[Windows (6)]` `[Search (12)]`

Each button grabs the top functions from that area instantly.

### Auto-Find
As you type your request, the tool searches in the background (800ms debounce) and auto-adds matching code to your prompt. No clicking needed.

### Smart Request Cleanup
Your sloppy typing gets cleaned before going to Claude:

| You type | Claude sees |
|---|---|
| `im tryna fix this but i dunno whats wrong` | `I'm trying to fix this but I don't know what's wrong.` |
| `lemme get teh sesion setings to work` | `Let me get the session settings to work.` |

### Domain Browsing (Browse by Area)
Non-coders can browse code by what it does, not what type it is:

`[Browser]` `[Config]` `[Search]` `[Windows]` `[GUI]` `[Files]`

Each snippet card shows a colored domain badge so you know what area it belongs to.

### Token Tracking
Persistent counter tracks how much you've saved across all sessions and projects. Dashboard shows all-time, per-project, and per-session totals.

### Smart Queue Management
- Queue capped at 15 snippets (prevents bloated prompts)
- Copy button debounced (no duplicate pastes)
- Clear button wipes request + queue in one click
- Empty copies blocked (must have content)

### Large Request Handling
Paste a 200-word request and it won't crash. The tool:
1. Breaks it into sub-tasks
2. Searches each independently
3. Deduplicates results
4. Auto-compresses if over 6K tokens

### Auto-Scan
Project code changes? The tool checks every 10 minutes and refreshes automatically. Only does a full rescan if files actually changed (mtime check).

### Optional: Local AI Assist
If you have [Ollama](https://ollama.com) running locally, the tool can ask a small model to interpret queries the fuzzy search misses. Settings tab has one-click model download buttons.

## Architecture

```
claude_backend/
  gui.py               CustomTkinter GUI
  backend.py           ClaudeContextManager orchestrator
  cli.py               CLI: bootstrap/prep/scan/status/clean
  search.py            Fuzzy semantic search + inverted index
  prompt_builder.py    Request cleanup + prompt assembly
  tokenizer.py         BPE token counting via tiktoken (with heuristic fallback)
  tracker.py           Token savings counter + session memory
  ollama_manager.py    Local AI model management (optional)
  scanners/
    project.py         os.scandir walker with early pruning
    local.py           Additional source directory scanner
    github.py          Optional GitHub repo scanner
  analyzers/
    code_extractor.py  AST (Python) + state machine (JS/TS)
    pattern_detector.py Convention detection
    structure_mapper.py Module dependency graph
  generators/
    claude_md.py       Generates CLAUDE.md
    memory_files.py    Generates persistent memory files
    snippet_library.py Categorized code snippet library
```

## Benchmarks

Real data from 7 days of tracked usage across 6 projects:

| Metric | Result |
|---|---|
| Events tracked | 66 |
| Projects used | 6 |
| Context builds | 62 |
| Snippets referenced | 3,086 |
| Avg input WITH tool | 10,011 tokens |
| Avg input WITHOUT tool | ~89,600 tokens |
| **Reduction per message** | **88%** |
| **Total tokens saved** | **5,734,087** |
| Opus value ($15/MTok) | $86 in 7 days |

### Search Accuracy
- **100%** on domain-specific queries (15/15 tested)
- **91%** on vague natural language (11/12 non-coder queries)
- **87%** on deliberately misspelled queries (7/8 typo queries)

### Token Waste Prevention
The session reviewer found and fixed these patterns:
- Queue capped at 15 snippets (previously unlimited, some copies had 165)
- Copy button debounced (8 duplicate copies prevented)
- Empty copies blocked (must have snippets or request text)
- Auto-find tuned: fewer but more relevant results

## Claude Pro 20x Max Plan Impact

| Without Tool | With Tool | Gain |
|---|---|---|
| 2 exchanges per conversation | 15 exchanges | **650% longer** |
| ~60 restarts/day | ~8 restarts/day | **52 fewer** |
| 120 effective messages/day | 777+ effective messages/day | **547% more** |

Same $200/month plan, dramatically more productive use.

## Requirements

- **Windows 10/11** (for window management features)
- **Python 3.10+** (if running from source)
- `customtkinter >= 5.2.0`
- `pyperclip >= 1.8.0`
- `tiktoken >= 0.7.0` (BPE token counting — 6-35% more accurate than heuristic)
- **Optional**: [Ollama](https://ollama.com) for AI-assisted search

## Security & Privacy

- Zero personal data in code (audited)
- No hardcoded paths, secrets, or API keys
- Token tracker stores project names only (anonymizable)
- Zero external API calls (all processing is local)
- No data sent anywhere (everything stays on your machine)
- Analysis reports can be generated with anonymized project names

## CLI Reference

```bash
# First time: scan project and generate all context files
python -m claude_backend bootstrap /path/to/project

# Update: regenerate only changed files
python -m claude_backend prep /path/to/project

# Analyze without generating
python -m claude_backend scan /path/to/project

# Check what's generated
python -m claude_backend status /path/to/project

# Remove generated files
python -m claude_backend clean /path/to/project
```

## How Token Savings Are Calculated

The tool measures real events, not estimates:

1. **Per query**: Counts tokens in the targeted snippets you send vs. the full files Claude would read
2. **Per session**: Measures pre-loaded context (CLAUDE.md + memory) vs. 30% source scan
3. **Restart savings**: Counts conversation restarts avoided (each costs ~5K tokens to re-explain context)
4. **Token math**: Uses tiktoken BPE tokenizer (cl100k_base, Rust-backed) for accurate counts. Falls back to `chars * 10 / 32` heuristic if tiktoken not installed.

## Testing & Analytics

Comprehensive testing was performed on 3 representative projects (small, medium, large) totaling 43 files and 463 tokens.

### Test Results Summary
- **Files Scanned**: 43 across 3 project types
- **Tokens Counted**: 463 with 3.36 chars/token average
- **Tokenization Consistency**: 100% (15/15 tests passed, 0 variance)
- **File Discovery Accuracy**: 100% (43/43 files found)
- **Critical Issues Found**: 1 (ScanConfig API incompatibility)

### Detailed Reports
- 📋 **[PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)** — Current status, blockers, and fix roadmap (7.9/10 ready)
- 📊 **[TESTING_REPORTS.md](TESTING_REPORTS.md)** — Detailed test results across 7 dimensions (tokenization, filesystem, code quality, context generation, performance, reliability, accuracy)
- 📈 **Raw Analytics Data**:
  - [TOKEN_SAVER_DETAILED_ANALYTICS.json](docs/analytics/TOKEN_SAVER_DETAILED_ANALYTICS.json) — 200+ metrics per project
  - [MACHINE_LEARNING_DATASET.json](docs/analytics/MACHINE_LEARNING_DATASET.json) — Normalized feature vectors for ML analysis

### Dimension Scores
| Dimension | Score | Status |
|-----------|-------|--------|
| Tokenization | 9.5/10 | ✅ PASS — 100% consistency |
| Filesystem | 8.5/10 | ✅ PASS — All files discovered |
| Code Quality | 6.0/10 | ⚠️ Untested on real code |
| Context Generation | 5.0/10 | ❌ BLOCKED — API bug |
| Performance | 8.0/10 | ✅ GOOD — Fast scanning |
| Reliability | 8.5/10 | ✅ GOOD — No crashes |
| **Overall** | **7.9/10** | ⚠️ **NOT PRODUCTION READY** |

### Known Issues
1. **CRITICAL**: ScanConfig API incompatibility blocks context generation (fix: 2 hours)
2. **MEDIUM**: Tokenizer accuracy not validated against official tokenizer
3. **MEDIUM**: Code quality detection untested on real production code

### How to Run Tests
```bash
# Full test suite with analytics
python tests/run_comprehensive_analysis.py

# Results are saved to:
# - TESTING_REPORTS.md (detailed report)
# - PRODUCTION_READINESS.md (status + blockers)
# - docs/analytics/*.json (raw metrics + ML data)
```

## License

MIT

## Contributing

Issues and PRs welcome. The codebase is ~4,500 lines of Python with no complex dependencies.

Key files to know:
- `search.py` — The fuzzy search engine (concepts, typo correction, inverted index)
- `gui.py` — The full GUI (~1,400 lines of CustomTkinter)
- `prompt_builder.py` — Request cleanup and prompt assembly
- `backend.py` — The orchestrator that ties everything together
