# Architecture Decision Document for NeoAutocoder (Exact Copy of Autocoder from Scratch)

## What We Keep (Core Fidelity to Original)
- **Core Loop**: Task → Engineered Prompt → AI Chat (via CDP) → DOM code extraction → Feed back with next improvement focus. Endless until stagnation or perfection.
- **8 Improvement Focuses**: Deep Code Dive, Extra Features, Pressure Test, Explore & Expand, Beautiful GUI, Solid & Functional, Reference Images, Review & Grade. (Will curate to 10-12 high-impact per tune-up skill to avoid proliferation).
- **Provider Chain & Fallback**: OpenRouter API → Gemini browser (CDP) → ChatGPT browser → Ollama local → Copilot browser. With cooldowns (120s failure, 300s rate-limit), success/failure tracking, model cycling.
- **Parallel Sessions**: Up to 4 simultaneous in screen corners (Win32 window placement).
- **Stagnation Detection**: MD5 hash comparison of extracted code. On plateau → expansion mode (companion modules).
- **State Persistence**: JSON + SQLite for stop/resume, Windows startup integration.
- **Broadcast Mode**: Send same task to all active sessions.
- **Smart Recovery**: Detect chat vs code response, reset conversation, self-diagnose.
- **Perfection Loop**: Cycle all focuses, auto-stop when no improvement.
- **Auto-save**: Every iteration to organized directory (not flat Downloads - per tune-up fix 8).
- **GUI**: CustomTkinter app with session cards, focus checkboxes, controls.
- **Session & ProviderEntry dataclasses**: Exact structure preserved for compatibility.

## What We Do Differently & Why (Addressing Known Pitfalls from ai-coding-pipeline-audit and autocoder-tune-up)

1. **Modular Design vs Monolithic broadcast.py (336KB)**:
   - **New**: Split into core_loop.py (heart of improvement loop), prompt_engineer.py, code_extractor.py, session_orchestrator.py, recovery_manager.py.
   - **Why**: Original monolith leads to death spirals, hard-to-debug oscillation. Smaller modules (target <50KB each) enable TDD, easier verification (per verify-before-done skill), and systematic-debugging. Reduces context bloat for future LLM reviews.

2. **Prompt Strategy (Incremental + Code-First + Identity Lock)**:
   - **New**: Every prompt enforces "CODE FIRST, then commentary. Output COMPLETE codebase in single ```python block". Strong project identity lock ("This is PROJECT_NAME. Do not change core concept"). Incremental language ("add/improve this aspect, keep all existing functionality").
   - **Why**: Fixes mission drift, oscillation from full-rewrites, extraction failures (review-before-code), and summarization wall. Per audit skill: raise HARD_LIMIT to 90_000, use retrieval_context before summarization, lower regression threshold to 0.3.

3. **Extraction & Validation**:
   - **New**: Hybrid regex + lightweight LLM-as-judge for extraction (fallback to vision_analyze on screenshots if DOM fails). Post-extraction: run basic syntax check + self-test stub. Reject if <30% size or hash identical for 3+ iters.
   - **Why**: Original regex frequently misses unfenced "Python" outputs or captures prose. Prevents death spirals (per tune-up fixes 4,5).

4. **Concurrency & CDP**:
   - **New**: asyncio + dedicated CDPConnection per session (isolated ports 9222-9225, user-data-dirs). Built-in auto-login for Gemini (per Fix 7). launch_cdp_sessions.py with --remote-allow-origins=* mandatory.
   - **Why**: Avoids thread GIL issues, CDP stalls (extend wait to 30s + reload fallback per Fix 6), Chrome crashes. Parallel sessions share a central state DB instead of duplicating codebases.

5. **State & Persistence**:
   - **New**: SQLite DB for iterations, hashes, metrics, focus history. JSON snapshots for quick resume. Organized output: ~/Downloads/neo_autocoder/<project>/iter_XXXX_focus_timestamp.py + .md review.
   - **Why**: File-based resume in original is fragile. Enables better stagnation/perfection detection and metrics (code growth trend, focus efficacy).

6. **Provider Chain Enhancements**:
   - **New**: Temperature cycling (0.5-0.9) and focus variation per provider to break identity loops (per Fix 9). API-first for OpenRouter (bypasses UI fragility).
   - **Why**: DeepSeek V3 identity loops and CDP UI drift are primary failure modes.

7. **GUI & UX**:
   - **New**: Add live metrics dashboard (code size chart, stagnation counter, focus efficacy heatmap). One-click "Perfection Mode".
   - **Why**: Original GUI is basic. This provides observability to prevent "death spiral" without constant manual monitoring.

**Overall Rationale**: This is a "battle-hardened" exact functional copy. It preserves the user experience and core algorithm while incorporating all lessons from 100+ iterations of the original (oscillation, extraction failures, CDP glitches, focus proliferation). Expected outcome: faster convergence, 5x fewer rejections, sustained codebase growth instead of 23-56K oscillation band.

**Non-goals**: Full multi-file project support (keep single primary file + companions in expansion). No LangChain bloat — pure Python + CDP/websockets.

Next: Implement modules below, starting with data structures and core loop.
