"""Broadcast mode — send a task to all active sessions and loop endlessly.

When enabled, the user types ONE task description and it gets:
1. Engineered into a proper prompt via Prompt Architect's engine
2. Sent to ALL active sessions (or selected ones)
3. After each session completes, it auto-feeds the next improvement round
4. Loops until the user clicks Stop or hits Ctrl+K

Each session works independently — they all start at the same time and
the Traffic Controller serializes their mouse access. The prompts are
customized per-session using the AI profile name for context.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from gemini_coder.task_manager import CodingTask, TaskStatus
from .auto_save import save_task_output

logger = logging.getLogger(__name__)

# Import prompt engine for prompt engineering
try:
    from prompt_engine import (
        generate_code_prompt,
        BUILD_TARGETS,
        ENHANCEMENTS,
    )
    PROMPT_ENGINE_AVAILABLE = True
except ImportError:
    PROMPT_ENGINE_AVAILABLE = False
    logger.warning("prompt_engine not found — prompts will be sent raw")


def _looks_like_code(text: str) -> bool:
    """Check if response contains code markers. Returns False when the AI
    has lost context and is producing random chat instead of code."""
    if not text or len(text.strip()) < 50:
        return False
    # Look for common code indicators
    markers = ["def ", "class ", "import ", "function ", "const ", "var ", "let ",
               "```", "return ", "if __name__", "#!/", "async ", "struct ", "#include",
               "from ", "self.", "console.", "print(", "for ", "while "]
    text_lower = text.lower()
    hits = sum(1 for m in markers if m.lower() in text_lower)
    return hits >= 2  # at least 2 code markers


def engineer_prompt(
    task: str,
    build_target: str = "PC Desktop App",
    enhancements: Optional[list[str]] = None,
    context: str = "",
) -> str:
    """Use Prompt Architect's engine to build a production-grade prompt.

    Takes a simple task like "Build a calculator" and expands it into
    a full engineered prompt with role, platform context, reasoning,
    constraints, and quality gates.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        return task

    if enhancements is None:
        enhancements = ["More Features + Robustness"]

    return generate_code_prompt(
        task=task,
        build_target=build_target,
        enhancements=enhancements,
        context=context,
        reasoning="Structured CoT (SCoT)",
        output_format="Code Only",
        constraint_presets=["Python Best Practices", "Robustness"],
    )


def engineer_improvement_prompt(
    task: str,
    iteration: int,
    ai_name: str = "",
) -> str:
    """Generate an improvement prompt for subsequent iterations.

    Cycles through different improvement focuses so each round
    makes the code meaningfully better in a different dimension.
    """
    improvement_focuses = [
        {
            "focus": "Add Features",
            "prompt": (
                "You previously wrote code for: {task}\n\n"
                "Now ADD 2-3 useful features a real user would want:\n"
                "- Config options, CLI arguments, settings\n"
                "- Logging, progress indicators\n"
                "- Input validation, helpful error messages\n"
                "- Any missing functionality\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Professional Polish",
            "prompt": (
                "Improve this code to look and feel professional:\n"
                "- Clean structure, consistent naming\n"
                "- Type hints, docstrings\n"
                "- Organized imports, __main__ block\n"
                "- Polished output/UI\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Robustness & Edge Cases",
            "prompt": (
                "Harden this code for real-world use:\n"
                "- Handle edge cases, empty input, missing files\n"
                "- Add retry logic, graceful shutdown\n"
                "- Resource cleanup, error handling\n"
                "- Validate all inputs\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Performance & Optimization",
            "prompt": (
                "Optimize this code:\n"
                "- Fix bottlenecks, use efficient data structures\n"
                "- Add caching where sensible\n"
                "- Minimize I/O and unnecessary computation\n\n"
                "Return the COMPLETE updated code."
            ),
        },
        {
            "focus": "Final Review & Expand",
            "prompt": (
                "Senior developer final review:\n"
                "- Ensure all features work together\n"
                "- Fix any remaining issues\n"
                "- Add usage examples in comments\n"
                "- Think about what ELSE this could do — add one more capability\n\n"
                "Return the FINAL, COMPLETE code."
            ),
        },
    ]

    idx = iteration % len(improvement_focuses)
    focus = improvement_focuses[idx]
    prompt = focus["prompt"].format(task=task)

    if ai_name:
        prompt = f"[You are {ai_name}] {prompt}"

    return prompt


try:
    from .smart_router import SmartRouter, SMART_ROUTER_AVAILABLE
except ImportError:
    SMART_ROUTER_AVAILABLE = False


@dataclass
class BroadcastConfig:
    """Configuration for a broadcast run."""
    task: str = ""
    build_target: str = "PC Desktop App"
    enhancements: list[str] = field(default_factory=lambda: ["More Features + Robustness"])
    context: str = ""
    session_ids: list[str] = field(default_factory=list)  # Empty = all active
    endless: bool = True
    max_iterations: int = 999  # Safety cap
    time_limit_minutes: int = 0  # 0 = no limit
    smart_route: bool = False  # Classify + split: free parts → Gemini, hard → Claude


class BroadcastController:
    """Broadcasts a task to multiple sessions and loops improvements.

    Usage:
        bc = BroadcastController(session_manager)
        bc.set_callbacks(on_output=..., on_status=...)
        bc.start(BroadcastConfig(task="Build a calculator"))
        # ... runs until bc.stop()
    """

    def __init__(self, session_manager) -> None:
        self._sm = session_manager
        self._running = False
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._iteration_counts: dict[str, int] = {}
        self._results: dict[str, str] = {}  # session_id -> latest actual result

        self._on_output: Optional[Callable] = None
        self._on_status: Optional[Callable] = None
        self._on_iteration: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def set_callbacks(
        self,
        on_output: Optional[Callable] = None,
        on_status: Optional[Callable] = None,
        on_iteration: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
    ) -> None:
        self._on_output = on_output
        self._on_status = on_status
        self._on_iteration = on_iteration
        self._on_complete = on_complete

    def start(self, config: BroadcastConfig) -> None:
        """Start broadcasting to all target sessions."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._iteration_counts.clear()
        self._threads.clear()

        # Determine target sessions
        if config.session_ids:
            sessions = [
                self._sm.get_session(sid)
                for sid in config.session_ids
                if self._sm.get_session(sid)
            ]
        else:
            sessions = self._sm.active_sessions

        if not sessions:
            logger.warning("No active sessions to broadcast to")
            self._running = False
            return

        # Engineer the initial prompt
        engineered = engineer_prompt(
            task=config.task,
            build_target=config.build_target,
            enhancements=config.enhancements,
            context=config.context,
        )

        if self._on_status:
            names = ", ".join(s.ai_profile.name for s in sessions)
            self._on_status(f"Broadcasting to {len(sessions)} sessions: {names}")

        logger.info("Broadcasting to %d sessions: %s",
                     len(sessions),
                     [s.display_name for s in sessions])

        # Model switching is done manually by the user before broadcast.
        # Auto-switching was unreliable (typed model names into chat input).
        # The UI shows a reminder: "Pick a different model on each window first."

        # Smart routing: single orchestrated thread instead of per-session
        if config.smart_route and SMART_ROUTER_AVAILABLE:
            t = threading.Thread(
                target=self._smart_route_loop,
                args=(sessions, config, engineered),
                daemon=True,
            )
            self._threads.append(t)
            t.start()
            return

        # Launch a thread per session
        for session in sessions:
            if not session.is_configured:
                logger.warning("Skipping unconfigured session: %s", session.display_name)
                continue

            t = threading.Thread(
                target=self._session_loop,
                args=(session, config, engineered),
                daemon=True,
            )
            self._threads.append(t)
            t.start()

    def stop(self) -> None:
        """Stop all broadcast loops."""
        self._stop_event.set()
        self._running = False

        # Stop all session executors
        for session in self._sm.sessions:
            if session.client:
                session.client.cancel()

        logger.info("Broadcast stopped")
        if self._on_complete:
            self._on_complete(dict(self._iteration_counts))

    def _save_result(self, session, task: str, iteration: int,
                     focus: str, result: str, start_time: float) -> None:
        """Save an iteration's actual result to Downloads."""
        try:
            title = f"{task[:40]}_iter{iteration}_{focus.replace(' ', '_')}"
            path = save_task_output(
                title=title,
                output=result,
                ai_name=session.ai_profile.name,
                corner=session.corner,
                elapsed_seconds=time.time() - start_time,
                iterations=iteration,
            )
            if path and self._on_status:
                self._on_status(f"Saved: {path.name}")
        except Exception as e:
            logger.warning("Auto-save failed for %s: %s", session.display_name, e)

    def _session_loop(self, session, config: BroadcastConfig, initial_prompt: str) -> None:
        """Run the endless improvement loop for one session."""
        sid = session.session_id
        ai_name = session.ai_profile.name
        self._iteration_counts[sid] = 0
        start_time = time.time()

        try:
            # Iteration 0: Initial build with engineered prompt
            if self._stop_event.is_set():
                return

            if self._on_output:
                self._on_output(
                    sid, "system",
                    f"[{ai_name}] Starting: {config.task}\n"
                    f"{'='*50}\n"
                )

            result = session.client.generate(
                prompt=initial_prompt,
                system_instruction=(
                    "You are an expert coding assistant. Write clean, complete, "
                    "production-ready code. No placeholders."
                ),
                on_progress=lambda t, s=sid: (
                    self._on_output(s, "code", t) if self._on_output else None
                ),
            )

            # Store actual result and auto-save
            self._results[sid] = result
            if self._on_output:
                self._on_output(sid, "result", result)
            self._save_result(session, config.task, 1, "Initial Build", result, start_time)

            self._iteration_counts[sid] = 1
            if self._on_iteration:
                self._on_iteration(sid, 1, "Initial Build", ai_name)

            # Improvement loop
            iteration = 1
            while not self._stop_event.is_set():
                # Check limits
                if iteration >= config.max_iterations:
                    break
                if config.time_limit_minutes > 0:
                    elapsed_min = (time.time() - start_time) / 60
                    if elapsed_min >= config.time_limit_minutes:
                        break

                improvement = engineer_improvement_prompt(
                    task=config.task,
                    iteration=iteration,
                    ai_name=ai_name,
                )

                focus_names = [
                    "Add Features", "Professional Polish",
                    "Robustness", "Performance", "Final Review & Expand"
                ]
                focus = focus_names[iteration % len(focus_names)]

                if self._on_output:
                    self._on_output(
                        sid, "system",
                        f"\n[{ai_name}] Improvement #{iteration + 1}: {focus}\n"
                        f"{'-'*40}\n"
                    )

                try:
                    result = session.client.generate(
                        prompt=improvement,
                        on_progress=lambda t, s=sid: (
                            self._on_output(s, "code", t)
                            if self._on_output else None
                        ),
                    )
                except Exception as e:
                    logger.warning("[%s] Improvement failed: %s", ai_name, e)
                    if self._on_output:
                        self._on_output(sid, "error", f"Error: {e}\n")
                    time.sleep(5)
                    continue

                # Context-loss guard: detect when AI stops producing code
                if result and not _looks_like_code(result):
                    logger.warning("[%s] Context loss detected at iteration %d — "
                                   "output has no code markers. Stopping loop.",
                                   ai_name, iteration + 1)
                    if self._on_output:
                        self._on_output(
                            sid, "system",
                            f"\n[{ai_name}] STOPPED: AI lost context — "
                            f"output at iteration {iteration + 1} contains no code. "
                            f"Last good output was iteration {iteration}.\n"
                        )
                    break

                # Store actual result and auto-save
                self._results[sid] = result
                if self._on_output:
                    self._on_output(sid, "result", result)
                iteration += 1
                self._save_result(session, config.task, iteration, focus, result, start_time)

                self._iteration_counts[sid] = iteration
                if self._on_iteration:
                    self._on_iteration(sid, iteration, focus, ai_name)

        except InterruptedError:
            logger.info("[%s] Broadcast cancelled", ai_name)
        except Exception as e:
            logger.error("[%s] Broadcast error: %s", ai_name, e)
            if self._on_output:
                self._on_output(sid, "error", f"[{ai_name}] Fatal: {e}\n")
        finally:
            count = self._iteration_counts.get(sid, 0)
            elapsed = time.time() - start_time
            logger.info("[%s] Broadcast loop ended: %d iterations in %.0fs",
                         ai_name, count, elapsed)

    def _smart_route_loop(
        self, sessions: list, config: BroadcastConfig, initial_prompt: str
    ) -> None:
        """Classify → split → send easy parts to free model → chain into Claude."""
        start_time = time.time()

        try:
            router = SmartRouter()
        except Exception as e:
            logger.error("SmartRouter init failed: %s — falling back to normal broadcast", e)
            for session in sessions:
                if session.is_configured:
                    self._session_loop(session, config, initial_prompt)
            return

        try:
            # 1. Classify
            cls = router.classify(config.task)
            if self._on_output:
                self._on_output("smart_route", "system",
                    f"[SmartRoute] Routing: {cls.routing.upper()} | "
                    f"Complexity: {cls.complexity_score:.2f} | "
                    f"Confidence: {cls.confidence:.2f}\n"
                    f"  Types: {', '.join(cls.task_types)}\n"
                    f"  Reasoning: {cls.reasoning}\n{'='*50}\n")

            # 2. Find sessions
            free_sess = router.find_free_session(sessions)
            claude_sess = router.find_claude_session(sessions)

            free_name = free_sess.ai_profile.name if free_sess else "none"
            claude_name = claude_sess.ai_profile.name if claude_sess else "none"
            logger.info("[SmartRoute] Free=%s, Claude=%s, routing=%s",
                        free_name, claude_name, cls.routing)

            # 3. Route based on classification
            if cls.routing == "free":
                target = free_sess or claude_sess or (sessions[0] if sessions else None)
                if target:
                    self._smart_run_single(target, config, initial_prompt, "Free", start_time)
                return

            if cls.routing == "claude":
                target = claude_sess or free_sess or (sessions[0] if sessions else None)
                if target:
                    self._smart_run_single(target, config, initial_prompt, "Claude", start_time)
                    # Enter improvement loop on Claude
                    if config.endless and not self._stop_event.is_set():
                        self._session_loop(target, config, initial_prompt)
                return

            # 4. Split mode — the main event
            rr = router.split(config.task, cls)

            if self._on_output:
                free_count = sum(1 for st in rr.subtasks if st.routing == "free")
                claude_count = sum(1 for st in rr.subtasks if st.routing == "claude")
                self._on_output("smart_route", "system",
                    f"[SmartRoute] Split: {free_count} free + {claude_count} claude subtasks\n"
                    f"  Free tokens: ~{rr.free_token_estimate:,} | Claude tokens: ~{rr.claude_token_estimate:,}\n"
                    f"  Savings: {rr.savings_pct:.0%}\n{'-'*40}\n")

            # 4a. Send free parts to Gemini
            free_response = ""
            if rr.free_prompt and free_sess:
                if self._on_output:
                    self._on_output(free_sess.session_id, "system",
                        f"[{free_name}] Handling free-model subtasks...\n")

                free_response = free_sess.client.generate(
                    prompt=rr.free_prompt,
                    system_instruction="Complete the task directly with clean, working code.",
                    on_progress=lambda t, s=free_sess.session_id: (
                        self._on_output(s, "code", t) if self._on_output else None),
                )
                self._results[free_sess.session_id] = free_response
                self._save_result(free_sess, config.task, 1,
                                  "SmartRoute_Free", free_response, start_time)

                if self._on_output:
                    self._on_output(free_sess.session_id, "result", free_response)

            elif rr.free_prompt and not free_sess:
                logger.warning("[SmartRoute] Free prompt exists but no free session — skipping")

            if self._stop_event.is_set():
                return

            # 4b. Send hard parts to Claude, enriched with free results
            if rr.claude_prompt and claude_sess:
                enriched = router.inject_free_results(rr.claude_prompt, free_response)

                if self._on_output:
                    self._on_output(claude_sess.session_id, "system",
                        f"[{claude_name}] Handling Claude subtasks "
                        f"(with {len(free_response):,} chars of free-model context)...\n")

                claude_response = claude_sess.client.generate(
                    prompt=enriched,
                    system_instruction=(
                        "You are an expert coding assistant. The easy parts were already "
                        "handled by a free model (included above). Focus on the complex "
                        "parts that require your expertise."
                    ),
                    on_progress=lambda t, s=claude_sess.session_id: (
                        self._on_output(s, "code", t) if self._on_output else None),
                )
                self._results[claude_sess.session_id] = claude_response
                self._save_result(claude_sess, config.task, 1,
                                  "SmartRoute_Claude", claude_response, start_time)

                if self._on_output:
                    self._on_output(claude_sess.session_id, "result", claude_response)

                # Save combined results
                from .auto_save import save_smart_route_output
                save_smart_route_output(
                    title=config.task,
                    free_output=free_response,
                    free_ai_name=free_name,
                    claude_output=claude_response,
                    claude_ai_name=claude_name,
                    classification_summary=(
                        f"{cls.routing} | complexity={cls.complexity_score:.2f} | "
                        f"types={','.join(cls.task_types)}"),
                    elapsed_seconds=time.time() - start_time,
                )

            elif rr.claude_prompt and not claude_sess:
                # No Claude session — send to whatever is available
                fallback = free_sess or (sessions[0] if sessions else None)
                if fallback:
                    logger.warning("[SmartRoute] No Claude session — using %s as fallback",
                                   fallback.ai_profile.name)
                    self._smart_run_single(fallback, config, rr.claude_prompt,
                                           "Fallback", start_time)

        except Exception as e:
            logger.error("[SmartRoute] Error: %s", e)
            if self._on_output:
                self._on_output("smart_route", "error", f"[SmartRoute] Fatal: {e}\n")
        finally:
            elapsed = time.time() - start_time
            logger.info("[SmartRoute] Completed in %.0fs", elapsed)
            self._running = False
            if self._on_complete:
                self._on_complete(self._iteration_counts)

    def _smart_run_single(
        self, session, config: BroadcastConfig, prompt: str,
        label: str, start_time: float
    ) -> None:
        """Send a prompt to a single session (used by smart routing)."""
        sid = session.session_id
        ai_name = session.ai_profile.name

        if self._on_output:
            self._on_output(sid, "system",
                f"[{ai_name}] SmartRoute → {label}\n{'='*50}\n")

        result = session.client.generate(
            prompt=prompt,
            system_instruction="Complete the task directly with clean, working code.",
            on_progress=lambda t, s=sid: (
                self._on_output(s, "code", t) if self._on_output else None),
        )
        self._results[sid] = result
        self._save_result(session, config.task, 1,
                          f"SmartRoute_{label}", result, start_time)
        if self._on_output:
            self._on_output(sid, "result", result)
